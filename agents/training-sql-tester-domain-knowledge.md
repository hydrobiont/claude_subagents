# Training SQL Tester — Domain knowledge

Persistent notes accumulated by the `training-sql-tester` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. SSH/YubiKey idiosyncrasies on stg-devpg-01-gcp-instance01, behaviors of the test cluster (extensions installed, default search_path), psql output formatting tricks for clean slide capture, recurring demo-failure causes, etc.

See the agent definition (`training-sql-tester.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### Key-access window: YubiKey-free SSH to the test VM — 2026-06-05
For intensive sessions the user deploys a temporary passwordless ed25519 key via `~/work/de/trainings2025/test-access/devpg-test-access.sh deploy` (registered in instance metadata — OS Login is off on `dba-test-430310`, so it propagates to `authorized_keys`). While it is deployed, reach `stg-devpg-01-gcp-instance01` with **no YubiKey**: `gcloud compute ssh … --tunnel-through-iap --ssh-key-file=~/work/de/trainings2025/test-access/id_devpg_test -- -o IdentitiesOnly=yes` then either `-N -L 5433:localhost:5432` (tunnel, then psql as `devpg_reader`) or `--command='sudo -u postgres psql …'` (superuser, for DML). `IdentitiesOnly=yes` is mandatory — without it ssh offers the agent's YubiKey PIV key and dies with `agent refused operation`. Check the window with `…/devpg-test-access.sh status`; the **user** opens it (`deploy`) and closes it (`remove`) — never do that yourself. Validated end-to-end on the dev-01 demo (reads as devpg_reader via the key tunnel + the rolled-back DML as postgres), all YubiKey-free. When the window is CLOSED, revert to the YubiKey tunnel/script flow.
