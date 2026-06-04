# Go Code Writer — Domain knowledge

Persistent notes accumulated by the `go-code-writer` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. Go-idiom decisions confirmed by the user, library choices that paid off, project-layout conventions in this user's repos that aren't yet baked into the agent prompt, version-specific gotchas, performance traps in pgx/Prometheus/OTel.

This file is the writer's view. The tester maintains a separate one at `go-test-engineer-domain-knowledge.md`; cross-reference but don't duplicate.

See the agent definition (`go-code-writer.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### `modernc.org/sqlite` driver name is plain `"sqlite"`, not `"sqlite3"`

The `_ "modernc.org/sqlite"` blank import registers the driver under the name `"sqlite"` for `database/sql.Open`, where C-backed `github.com/mattn/go-sqlite3` registers `"sqlite3"`. Easy to swap drivers later, but the literal name differs — grep for `sql.Open("sqlite"` (not `"sqlite3"`) when porting code between the two.

### In-memory SQLite + `database/sql` requires `SetMaxOpenConns(1)`

A `sql.Open("sqlite", ":memory:")` gets you a per-connection database. `database/sql`'s pool will happily hand out fresh connections on the next call, each seeing an empty database. For test/in-memory use you must pin the pool to one connection (or use `cache=shared` with a `file::memory:?cache=shared` DSN, which is less hermetic). For on-disk WAL we still set `SetMaxOpenConns(1)` to enforce a single-writer contract — the project pattern.

### `go get <dep>@<newer>` on a same-`go-directive` dep is a quiet success

When the dep's `go.mod` requires the same Go directive as the consumer (here both `1.25.0`), `go get` bumps cleanly without rewriting the directive. The pgx-style silent bump only fires when the dep raises the floor. Worth distinguishing in the writer report so the user isn't surprised by either case.

### `go get` silently bumps the module's `go` directive to match the dep's minimum

Running `go get github.com/jackc/pgx/v5@v5.9.2` against a `go 1.22` module rewrote the `go` directive in go.mod to `1.25.0` (pgx v5.9.x requires Go 1.25). No warning, no confirmation prompt. The bump is real — it forces every future consumer of the module onto Go ≥ 1.25 — and reads like a Claude mistake when reviewers compare before/after. Always check the dep's `go.mod` (`cat ~/go/pkg/mod/<path>@<ver>/go.mod | head`) before pinning a version, and call the toolchain bump out explicitly in the writer report so the user can choose between (a) accepting it or (b) downgrading to an older line still on the project's Go floor (e.g. pgx v5.7.4 supported Go 1.21).

### `pgx/v5` defaults `DefaultQueryExecMode` to `QueryExecModeCacheStatement` already

The extended/prepared protocol with statement caching is pgx v5's out-of-the-box default — see the `defaultQueryExecMode := QueryExecModeCacheStatement` switch at the top of `conn.go`. Setting `cfg.ConnConfig.DefaultQueryExecMode = pgx.QueryExecModeCacheStatement` in pgxpool config is belt-and-suspenders, but still worth doing: it makes the intent explicit at the call site so a future config change or env-driven override (`PGOPTIONS`, etc.) cannot silently drop the pool into simple-protocol mode.

### `signal.NotifyContext` doesn't surface the signal via `context.Cause`

When a `ctx` produced by `signal.NotifyContext` is cancelled by an incoming signal, `context.Cause(ctx)` returns the generic `context.Canceled` — not the signal name. Stdlib (as of Go 1.22–1.25) doesn't attach the originating `os.Signal` to the cancellation cause. If you want to log which signal triggered shutdown, install your own `signal.Notify` channel alongside or layer a `context.WithCancelCause` wrapper that records the signal before cancelling.

### `go build ./...` from a `cmd/` module writes a binary into cwd

Running `go build ./...` (no `-o`) from a repo whose `main` package lives under `cmd/<name>` deposits the binary in the *current* working directory, not in the package dir. Easy to leave a stray artifact in the source tree during verification. Either build the specific package with `-o bin/<name> ./cmd/<name>` (what the Makefile should do) or clean up after `./...` builds.

### `go run` swallows signals sent to the wrapper, not the child

Verifying SIGINT/SIGTERM handlers via `go run ./cmd/foo & kill -INT $!` tests the `go run` driver process, not the program's own signal handler — the child receives a forced kill (exit 143 on TERM, no graceful logs on INT). For real shutdown verification, `go build -o bin/foo ./cmd/foo` first and signal the built binary.

