# Go Test Engineer — Domain knowledge

Persistent notes accumulated by the `go-test-engineer` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. testing patterns confirmed by the user, testcontainers/dockertest quirks, prometheus/testutil APIs that work well, time-mocking patterns this codebase prefers, recurring testability problems in the writer's output, golden-file gotchas, fuzzing seed strategies.

This file is the tester's view. The writer maintains a separate one at `go-code-writer-domain-knowledge.md`; cross-reference but don't duplicate.

See the agent definition (`go-test-engineer.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### A `decodeX(s string)` with an `if s == ""` "tolerate NULL" branch is a lie if the caller `rows.Scan`s into a plain `string`

Classic doc-vs-code bug worth probing whenever a read path claims to "tolerate a NULL cell → nil/empty". `database/sql` refuses to scan SQL `NULL` into a `string` (or `int`, etc.) — `rows.Scan` fails with `converting NULL to string is unsupported` *before* any decode helper's empty-string guard runs. So a helper's `if s == ""` branch only ever fires for a genuinely empty-string cell (`''`), never for `NULL`; the NULL path is a scan error the godoc never mentions. To pin all three states distinctly, inject rows via a *second* `*sql.DB` on the same SQLite file (WAL makes the committed row visible to the bundle's own writer conn) with `payload any`: pass `"{}"` (→ empty non-nil map), `""` (→ nil map, the guard fires), and `nil` (→ genuine SQL NULL → scan error = the bug). The fix is the writer's: scan into `sql.NullString` and map `!Valid` to nil. Confirmed on modernc.org/sqlite; same on mattn.

### Golden-file `-update` flow + verifying goldens on macOS (`cat -A` is GNU-only)

Standard golden harness that worked cleanly: `var update = flag.Bool("update", false, ...)`; `assertGolden` renders to a `bytes.Buffer`, and under `-update` does `os.MkdirAll("testdata")` + `os.WriteFile(path, got, 0644)` and returns, else `os.ReadFile` + `bytes.Equal` (byte-exact is the point — don't reach for go-cmp on a `[]byte`). Generate once with `go test ./pkg -run Golden -update`, then run without the flag to prove compare-mode. To *inspect* the generated goldens for hidden chars on darwin, `cat -A` fails (`illegal option -- A`) — use `sed -n l FILE` instead; it shows `$` at line ends and escapes control bytes (note it also hard-wraps at ~70 cols with a trailing `\`, which is display-only, not file content). Pair the golden with a couple of non-golden assertions (sort order, escape transforms) so a regenerated-with-wrong-behavior golden still trips a named test.

### Capturing `run([]string, stdout, stderr *os.File) error` output: os.Pipe + concurrent drain

When a CLI entrypoint is refactored to take `*os.File` writers (not `io.Writer`) so `main` stays a thin `os.Exit` boundary, test it by handing it two `os.Pipe()` write-ends, draining both read-ends in goroutines (`io.ReadAll` → channel) *before* calling `run`, then closing the write-ends and receiving. The concurrent drain matters even for small output — a synchronous read after a blocking write would deadlock if output ever exceeds the pipe buffer. This keeps the test refactor-free (no swapping the signature to `io.Writer` or `*bytes.Buffer`). `main()` itself stays at 0% coverage (it calls `os.Exit`) — that's expected and correct; all logic lives in `run`, which reaches 100%.

### A struct with a map field is not comparable — `v != Struct{}` is a compile error; write a field-wise `assertZeroVerdict`

To assert a "could not run" path returns the zero struct, the instinct is `if v != (pkg.Foo{})`. If `Foo` has a map field (e.g. `checks.Verdict{ Payload map[string]any }`) the struct is **not comparable** and this is a build/vet failure, not a runtime one. Two traps in one: (1) `go vet` reports it confusingly as `expected boolean expression, found assignment (missing parentheses around composite literal?)` — nothing to do with parentheses; the real cause is non-comparability. (2) A composite literal as the *init clause* of an `if` (`if _, err := (Foo{}).Method(); …`) genuinely does need parens — `Foo{}` there is parsed as a block — so you can hit the *same* vet message for the *other* reason on an adjacent line. Fix for the map case: a helper that checks each field (`Name==""`, `Severity==0`, `Timestamp.IsZero()`, `Message==""`, `Payload==nil`). Fix for the init-clause case: wrap the literal `(Foo{}).Method()`.

### White-box `package builtin` test triggers the package's own `init()` — assert `DefaultRegistry()` directly, never `Register` into it

When self-registering checks populate a process-wide `checks.DefaultRegistry()` from `init()`, an in-package test file (`package builtin`, not `builtin_test`) has already run those inits by the time any test executes — so `DefaultRegistry().All()` is the live, ordered trio and you assert names/order/timeouts straight off it. Do NOT `Register` into the default registry from a test: the registry panics on duplicate names and the singleton is shared across the whole test binary, so a second registration of an already-registered name aborts the run. Read-only (`All`, `Lookup`) is safe and parallel-friendly.

### `os.ReadFile` on a directory returns a non-`IsNotExist` error — the clean seam for testing the "other read error" branch

A file-reading check typically forks on `os.IsNotExist(err)`: missing file → graceful/degraded verdict, any other error → "could not run". To hit the *other* branch deterministically without root or chmod tricks, point the path at a directory: `os.ReadFile(t.TempDir())` fails with `EISDIR` ("is a directory") for which `os.IsNotExist` is **false** (verified on darwin). For the missing-file branch, use `filepath.Join(t.TempDir(), "does-not-exist")` so `IsNotExist` is true. Both are hermetic and need no privileges.

### Point-a-package-var-at-a-fixture pattern: save/restore in a `t.Cleanup` helper, keep those subtests serial

When production exposes a filesystem path as a package `var` (not const) precisely so tests can redirect it (`var thpEnabledPath = "/sys/…"`), the clean idiom is a helper `withXPath(t, path){ prev := X; X = path; t.Cleanup(func(){ X = prev }) }` feeding a `t.TempDir()` fixture. Because the var is shared mutable global state, those subtests must NOT `t.Parallel()` — run them serial and only parallelize the *pure-input* helper tests (e.g. the unexported line-parser) in the same file. This cleanly separates "table over fixture files, serial" from "table over strings, parallel" within one `_test.go`.

### `go test` runs `go vet` first — a `Test<lowercase>` name is a build-time failure, not a skip

`go test` runs a subset of `go vet` before compiling, and one of its checks (`tests`) rejects a test function whose first letter after `Test` is lowercase: `Testitoa has malformed name: first letter after 'Test' must not be lowercase` → `[build failed]`, exit 1. This bites when you white-box-test an unexported helper and instinctively name the test after it (`func Testitoa`). Fix: capitalize the segment (`TestItoa`) even though it no longer matches the helper's identifier — the mismatch is fine, vet's rule is not negotiable without `-vet=off`. Same class of vet-in-test gotcha as malformed `Benchmark`/`Example` names.

### Covering an unexported int→string / enum helper: white-box direct test beats going through `String()`

When an enum's `String()` switch returns named tokens for every *defined* value and only falls through to a shared `unknown(<n>)` helper for out-of-range input, the helper's `n == 0` branch is unreachable through the public API — every zero value hits a named `case` first. `go tool cover -func` will sit at ~94% on that helper forever via black-box tests. Because the helper is unexported and in-package, a direct table test (`TestItoa`, `TestUnknownString`) cross-checked against `strconv.Itoa` closes it to 100% without exporting anything or adding a seam. This is legitimate white-box coverage, not cheating — the helper has a real contract (handles `math.MinInt` via `u := uint(n); u = -u`) worth pinning independently of the enums that currently call it.

### Cross-compile (`GOOS=linux go test -c -o /dev/null`) to prove build-tagged files on the other platform aren't broken

On darwin you cannot *run* a `//go:build linux` file's tests, but you CAN prove they (and your new tests) compile against that platform's source set: `GOOS=linux GOARCH=amd64 go test -c -o <tmp> ./pkg/` builds the test binary without running it. Pair with `GOOS=linux go list -f '{{.GoFiles}}' ./pkg/` to confirm which tagged file (`probe_linux.go` vs `probe_other.go`) is selected per GOOS. Report this: it tells the user their Linux-only probe path is at least syntactically sound and that the portable tests will exercise it on Linux CI, even though local coverage on darwin only reflects the `!linux` file.

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
