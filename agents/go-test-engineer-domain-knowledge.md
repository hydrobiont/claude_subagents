# Go Test Engineer — Domain knowledge

Persistent notes accumulated by the `go-test-engineer` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. testing patterns confirmed by the user, testcontainers/dockertest quirks, prometheus/testutil APIs that work well, time-mocking patterns this codebase prefers, recurring testability problems in the writer's output, golden-file gotchas, fuzzing seed strategies.

This file is the tester's view. The writer maintains a separate one at `go-code-writer-domain-knowledge.md`; cross-reference but don't duplicate.

See the agent definition (`go-test-engineer.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### `pgxpool.NewWithConfig` is lazy — `New(ctx, dsn)` does not connect

A `pgxadapter.New`-style wrapper around `pgxpool.NewWithConfig` does **not** dial the database. Construction validates the connstring (via `pgxpool.ParseConfig`) and stages the pool; the first dial happens on the first query/acquire. Concrete consequences for tests:
- `TestNew_UnreachableHost` against `127.0.0.1:1` **does not** return an error from `New`; the test must follow up with `Query`/`Exec`/`Ping` to see the dial failure surface.
- `TestNew_EmptyConnString` succeeds — pgx falls back to libpq env vars (`PGHOST`, `PGUSER`, …). If your contract says "empty should be rejected", you need an explicit guard in `New`; otherwise pin the acceptance behavior with a test that fails loudly the moment policy changes.

### `pgxpool.Pool.Close` is idempotent and does NOT panic in v5

`pgxpool.Pool.Close()` can be called multiple times safely — second call is a no-op, no panic. After Close, `pool.QueryRow(...).Scan(&n)` returns the error string `"closed pool"` (raw, not wrapped). Adapter code that wraps `Exec`/`Query` will produce e.g. `"pgxadapter: exec: closed pool"`. This contradicts docs that say "calls after Close panic the way pgxpool does" — actual v5 behavior is well-behaved errors. Worth pinning with a test if your codebase relies on either flavor.

### Live-PG smoke tests gated on a DSN env var — the right shape for thin driver adapters

For a small driver-adapter package (a few methods that delegate to pgx/database-sql), neither testcontainers nor brittle pgx-interface mocking is worth it. The right shape is: skip-by-default smoke tests gated on a `*_TEST_DSN` env var via `t.Skip("…not set; skipping live-PG test")`. Default CI runs the no-DSN subset (typically 50–70% coverage — wrapper-construction paths only); an integration job sets the env var and gets full coverage (95%+). Don't drive CI gates off the no-DSN number — gate the integration job instead, and accept the no-DSN run is mostly a "skips cleanly" check.

### `pg_sleep(N)` returns `void` — un-scannable; use `SELECT 1 FROM pg_sleep(N)`

`SELECT pg_sleep(0.001)` produces a single column of type `void`, which pgx cannot Scan into anything sensible (`float64` fails with `strconv.ParseFloat: parsing "": invalid syntax`). For tests that want a server-side sleep with a scannable result, write `SELECT 1 FROM pg_sleep(0.001)` and `Scan(&n int)`. Otherwise use `Exec` and discard the tag.

### Testing unexported SQL constants — capture via fake, don't export

When a package has an unexported SQL constant (e.g. `detectQuery = "SELECT current_setting(...)"`) you want to pin literally, the temptation is to either (a) export it for the test, or (b) duplicate the literal in the test and trust they stay in sync. Both are wrong. The right move: define a fake `QueryRow(ctx, sql, args ...any)` that captures `sql` into a struct field, run the production code, then assert `fake.sql == "<expected literal>"`. The literal lives once in production and once in the test — that's not duplication, that's the contract. Also assert `len(args) == 0` (or the expected positional args) so a future refactor that adds parameters trips a test rather than silently changing the wire format. Bonus: capture `ctx` in the same fake and you get a context-propagation test for free.

### `context.DeadlineExceeded` is a sentinel `error` — useful for testing race between panic vs. timeout

`context.DeadlineExceeded` is a package-level sentinel `error` value, so it can be `panic(...)`-ed and then asserted against three different ways: as `recover()`'s `any`, via `errors.Is` after re-wrap, and via raw identity (`err == context.DeadlineExceeded`). This is handy when testing a runner that wraps user code with `defer recover()` *and* a per-call `context.WithTimeout` — you can author a test where the user code waits for `<-ctx.Done()` and then `panic(context.DeadlineExceeded)`, and verify that the runner's "route by `checkCtx.Err()` first, panic second" precedence holds. The wrapped-error variant (`fmt.Errorf("wrap: %w", context.DeadlineExceeded)`) is also worth pinning separately, because a careful runner returns `checkCtx.Err()` (raw sentinel) not the user's wrapped value — assert with both `errors.Is` and `==` to lock identity.

### modernc.org/sqlite version gate on the Go directive

`modernc.org/sqlite` since around v1.40 declares `go 1.25.0`, which forces the consuming project's `go.mod` directive up to 1.25. If the project pins an older directive (e.g. Go 1.22) and you need this driver as a test dep, pick the highest compatible release — v1.34.5 still declares `go 1.21` and pulls libc/sys versions that don't bump the directive. The chain that needs minimum-version selection: `modernc.org/sqlite@v1.34.5` → `modernc.org/libc@v1.61.6` → `golang.org/x/sys@v0.22.0` — all friendly to `go 1.22`. Also note: `go get`/`go mod tidy` only *raises* the `go` directive automatically; if you downgrade deps, manually edit the directive back down and re-run `go build ./...` to confirm.

### `:memory:` SQLite is per-connection — pin `MaxOpenConns=1` in tests

`database/sql` runs a connection pool by default. An in-memory SQLite database opened via `sql.Open("sqlite", ":memory:")` lives inside the *checked-out connection*; the pool can hand you a fresh, empty database on the next query. Symptom: `Exec(Schema)` succeeds, the next `QueryRow` against `sqlite_master` returns zero rows. Fix: `db.SetMaxOpenConns(1)` immediately after `sql.Open`. Alternative is the `file::memory:?cache=shared&_pragma=…` URI form, but the single-conn pin keeps tests hermetic. This bites with `modernc.org/sqlite` and `mattn/go-sqlite3` alike — the driver is innocent; the pool is the trap.

### `t.Parallel` subtests cannot share a `*sql.DB` fixture with `MaxOpenConns=1`

Once you pin the pool to one connection (above), three `t.Parallel` subtests that all hit the same `*sql.DB` will serialize on that one conn anyway — `database/sql` blocks on `db.Conn` until the previous query releases. Correctness-wise it's fine; it just doesn't buy parallelism. More importantly, if any subtest holds a `*sql.Rows` open across a yield, the other subtests stall. Cleaner: leave subtests that share a DB fixture serial, and only mark the *outer* test `t.Parallel`. If you genuinely need parallel readers, give each its own DB (call the open helper inside the subtest).
