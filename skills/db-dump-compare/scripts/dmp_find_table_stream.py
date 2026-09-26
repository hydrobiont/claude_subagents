#!/usr/bin/env python3
"""Locate a table's data stream inside Oracle Data Pump .dmp files and dump its readable strings.

Why: Data Pump metadata (DDL) is zlib-compressed by default (COMPRESSION=METADATA_ONLY),
but table DATA is written uncompressed unless COMPRESSION=ALL/DATA_ONLY was used. Every
table's data stream starts with an uncompressed XML header
  <STRMTABLE_T>...<OWNER_NAME>X</OWNER_NAME><NAME>T</NAME>...<COL_LIST>...</STRMTABLE_T>
followed by the rows. VARCHAR2 values are readable with a printable-strings scan, so small
configuration / version / Liquibase-changelog tables can be read without an Oracle instance.
DATE/NUMBER columns are binary and are NOT decoded here.

Sequential full read of every file given (176 GB took ~5 min on a laptop SSD). Read-only.

Usage:
  dmp_find_table_stream.py --owner PASX --table DATABASECHANGELOG [--table T2 ...] \
      --out DIR [--max-bytes 3000000] file1.dmp file2.dmp ...
"""
import argparse, os, re, sys, time

printable = re.compile(rb"[\x20-\x7e\t]{4,}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+"); ap.add_argument("--owner", required=True); ap.add_argument("--table", action="append", required=True)
    ap.add_argument("--out", default="."); ap.add_argument("--max-bytes", type=int, default=3_000_000); ap.add_argument("--chunk-mb", type=int, default=64)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pats = {t.upper(): f"<OWNER_NAME>{a.owner.upper()}</OWNER_NAME><NAME>{t.upper()}</NAME>".encode() for t in a.table}
    hits = []; CH = a.chunk_mb << 20; OV = 4096; t0 = time.time(); done = 0
    total = sum(os.path.getsize(f) for f in a.files)
    for fn in a.files:
        sz = os.path.getsize(fn)
        with open(fn, "rb", buffering=0) as f:
            pos = 0; prev = b""
            while pos < sz:
                buf = f.read(CH)
                if not buf: break
                data = prev + buf; base = pos - len(prev)
                for tname, p in pats.items():
                    i = 0
                    while (j := data.find(p, i)) >= 0:
                        off = base + j
                        if (fn, tname, off) not in hits:
                            hits.append((fn, tname, off)); print(f"HIT {os.path.basename(fn)} offset={off} {tname}", flush=True)
                        i = j + 1
                prev = data[-OV:]; pos += len(buf); done += len(buf)
                if (done // CH) % 64 == 0:
                    print(f"  scanned {done / (1 << 30):.1f} / {total / (1 << 30):.1f} GB ({done / max(time.time() - t0, 1) / (1 << 20):.0f} MB/s)", file=sys.stderr, flush=True)
    print(f"scan complete: {len(hits)} hits in {time.time() - t0:.0f}s", flush=True)
    for fn, tname, off in hits:
        with open(fn, "rb") as f:
            f.seek(off); blob = f.read(a.max_bytes)
        # cut at the next table's stream header so only this table's rows remain
        nxt = blob.find(b"<STRMTABLE_T>", 1)
        truncated = nxt < 0
        if nxt > 0: blob = blob[:nxt]
        out = os.path.join(a.out, f"{tname}_{os.path.basename(fn)}_{off}.strings.txt")
        with open(out, "wb") as o:
            for m in printable.finditer(blob): o.write(m.group(0) + b"\n")
        print(f"wrote {out} ({len(blob)} bytes of stream{'; TRUNCATED at --max-bytes, raise it' if truncated else ''})", flush=True)


if __name__ == "__main__":
    main()
