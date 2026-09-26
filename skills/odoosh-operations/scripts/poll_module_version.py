#!/usr/bin/env python3
"""
poll_module_version.py - poll an Odoo database over XML-RPC until a
module's installed_version reaches an expected value, or a timeout elapses.

Use this right after a production (or staging) fast-forward push: odoo.sh
restarts the build to load the new manifest version, and the origin
answers HTTP 503 for a short window during that restart. This script
tolerates that window - and ordinary connection errors - instead of
treating the first failed poll as proof the deploy failed. A successful
`git push` is not itself evidence the update landed; this readback is.

stdlib only (argparse, socket, ssl, subprocess, sys, time, xmlrpc.client).
Reads the API key from the macOS keychain at call time and never prints it.

Example:
    python3 poll_module_version.py \\
        --url https://dataegret.odoo.com \\
        --db dataegret-odoo-prod-34639522 \\
        --module de_fin_mail \\
        --expect 19.0.1.3.1

Exit status: 0 when the expected version is observed, 1 on timeout,
2 on a usage/setup error (bad args, keychain read failure).
"""
import argparse
import socket
import ssl
import subprocess
import sys
import time
import xmlrpc.client
from datetime import datetime, timezone


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def read_keychain_password(service: str, account: str) -> str:
    """Read a credential from the macOS keychain. Never logs or returns
    it anywhere except to the caller in memory."""
    try:
        completed = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit(
            "poll_module_version.py: the 'security' command is not available - "
            "this script expects to run on macOS, where credentials live in the keychain."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"poll_module_version.py: could not read keychain service {service!r} "
            f"for account {account!r} (security exited {exc.returncode}). "
            "Confirm the service/account names are right and that this process "
            "is allowed to read that keychain item."
        ) from exc
    return completed.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--url", required=True, help="base URL, e.g. https://dataegret.odoo.com")
    parser.add_argument("--db", required=True, help="database name, e.g. dataegret-odoo-prod-34639522")
    parser.add_argument("--module", required=True, help="technical module name, e.g. de_fin_mail")
    parser.add_argument("--expect", required=True, help="expected installed_version string, e.g. 19.0.1.3.1")
    parser.add_argument("--login", default="ik@dataegret.com", help="Odoo login (default: %(default)s)")
    parser.add_argument(
        "--keychain",
        default="odoo-sh-dataegret-api",
        help="macOS keychain service name holding the API key (default: %(default)s)",
    )
    parser.add_argument("--timeout", type=int, default=480, help="give up after this many seconds (default: %(default)s)")
    parser.add_argument("--interval", type=int, default=30, help="seconds between polls (default: %(default)s)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    password = read_keychain_password(args.keychain, args.login)

    common = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/common")
    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")

    log(
        f"polling {args.url} db={args.db} module={args.module} "
        f"expect={args.expect!r} every {args.interval}s, timeout {args.timeout}s"
    )

    deadline = time.monotonic() + args.timeout
    attempt = 0
    uid = None

    while time.monotonic() < deadline:
        attempt += 1
        try:
            if uid is None:
                uid = common.authenticate(args.db, args.login, password, {})
                if not uid:
                    log(f"attempt {attempt}: authenticate() returned a falsy uid - "
                        f"check --db/--login, this is not the 503 restart window")
                    time.sleep(args.interval)
                    continue

            rows = models.execute_kw(
                args.db, uid, password,
                "ir.module.module", "search_read",
                [[("name", "=", args.module)]],
                {"fields": ["name", "installed_version", "state"]},
            )
            if not rows:
                log(f"attempt {attempt}: no ir.module.module row named {args.module!r} on this database")
            else:
                row = rows[0]
                version = row.get("installed_version")
                state = row.get("state")
                log(f"attempt {attempt}: {args.module} state={state!r} installed_version={version!r}")
                if version == args.expect:
                    log(f"reached expected version {args.expect!r} - done")
                    return 0

        except (socket.timeout, ConnectionError, OSError, ssl.SSLError) as exc:
            log(f"attempt {attempt}: connection error, tolerating (likely mid-restart): {exc}")

        except xmlrpc.client.ProtocolError as exc:
            # odoo.sh answers 503 (and sometimes 502/500) during the restart
            # window; that is expected here, not a reason to stop.
            expected = exc.errcode in (500, 502, 503)
            level = "expected during a restart" if expected else "NOT a normal restart code - investigate if this persists"
            log(f"attempt {attempt}: HTTP {exc.errcode} ({level}): {exc.errmsg}")

        except xmlrpc.client.Fault as exc:
            first_line = exc.faultString.splitlines()[0] if exc.faultString else str(exc)
            log(f"attempt {attempt}: XML-RPC fault, tolerating and retrying: {first_line}")
            uid = None  # re-authenticate next time in case the fault was session-related

        time.sleep(args.interval)

    log(f"timeout after {args.timeout}s without observing installed_version == {args.expect!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
