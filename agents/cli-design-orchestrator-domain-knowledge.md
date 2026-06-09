# CLI Design Orchestrator — Domain knowledge

Persistent notes accumulated by the `cli-design-orchestrator` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable — CLI design decisions the user confirmed, library choices that paid off, roster facts (which agents cover what), harness gotchas about creating/invoking agents, project-layout conventions.

See the agent definition (`cli-design-orchestrator.md`) for what belongs here vs not. Keep it generic — one product's specifics belong in that project's `CLAUDE.md` or in a dedicated domain agent, not here.

<!-- entries below; newest on top -->

### Bubble Tea v2 TUI: testable model/update/view + injected seams (verified 2026-06-08, bubbletea/v2 v2.0.7, lipgloss/v2 v2.0.3, Go 1.25)

Built cal_agent's `internal/tui` (app shell + free-slots pane) plus the `internal/app` data-loader bridge and `internal/clipboard`. Patterns that tested cleanly with zero TTY/network/Keychain/clipboard:
- **Make the network+compute a single injected `LoadFunc`.** The model holds `load func(weekOffset int) (Week, []Warning, error)` and `clip Clipboard` as fields. Production wires the real Google-backed loader (in a `cmd_tui.go` in `main`, the only place the concrete client/Keychain/pbcopy bind); tests pass a synchronous fake loader + recording clipboard. The whole `Update` is then driven with synthetic msgs and asserted on resulting model state — no `p.Run()`, no terminal.
- **Async load = a `tea.Cmd` closure, never inline.** `loadCmd(offset)` captures `m.load` and returns `func() tea.Msg { ... return weekLoadedMsg{offset,...} | loadErrMsg{offset,...} }`. Tag every result msg with the offset it was for and **drop stale results** (`if msg.offset != m.weekOffset { return m,nil }`) so a slow week-N fetch landing after the user arrowed to week-N+1 doesn't clobber state. Test it: arrow right, feed a weekLoadedMsg for the old offset, assert still-loading.
- **Constructing `tea.KeyPressMsg` in tests:** `.String()` is driven by `Code`/`Mod`, NOT `Text`. `{Text:"up"}` does NOT yield "up". Use `{Code: tea.KeyUp}` → "up"; `{Code: tea.KeySpace}` → "space" (NOT " "); `{Code:'c', Mod: tea.ModCtrl}` → "ctrl+c"; printable letters `{Code:'q', Text:"q"}` → "q". A 10-line probe binary confirmed the exact strings — do that once per project. Corollary: in the Update switch, match `case "space"` not `case " "`.
- **`tea.Tick(d, fn)` exists in v2** for the transient-status-clear timer (copy confirmation auto-dismiss). `tea.WindowSizeMsg{Width,Height}` for responsive layout. Lip Gloss v2 API used: `lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("12")).Faint(true).Render(s)`, `lipgloss.JoinVertical(lipgloss.Left, parts...)` — color is `lipgloss.Color(string)` returning `color.Color` (Foreground takes a `color.Color`).
- **Componentize View now even when only one pane exists.** `View()` = `JoinVertical(header, "", pane, "", status, "", helpbar)` with each `render*()` a method. The agenda/grid/to-do panes and accounts sidebar drop into the same join later without reworking the shell. Keep cursor/selection as **indices into the flat slot list** (`Week.Flat`), reset on week change (indices are week-relative). `y` with empty multi-select falls back to the cursor slot — nice default.
- **Data-loader bridge belongs in its own `internal/app`, not in google or freeslots.** It depends on a `CalendarClient` interface (subset of `*google.Client`: just `BusyIntervals`) + a `ClientFactory func(ctx,account)(CalendarClient,error)`. `LoadBusy` iterates accounts → visible calendars, and a **per-account factory error (ErrReauthorize) becomes a collected `Warning`, not a fatal** — other accounts still load. A per-calendar fetch error likewise warns-and-skips that one calendar. Test with a fake factory + fake client recording queried IDs: assert hidden calendars are never queried, both accounts' busy is gathered, and an auth-failing account yields exactly one reauthorize Warning while the other still returns data. Highest-value seam in the increment.

### Clipboard behind a 1-method interface; pbcopy via exec, command construction is the testable seam (cal_agent, 2026-06-08)

`type Clipboard interface { Copy(text string) error }`. macOS impl = `exec.CommandContext(ctx,"pbcopy")` with `cmd.Stdin = strings.NewReader(text)` then `cmd.Run()` — no new dependency (chose this over atotto/clipboard; simplest reliable macOS path, and DESIGN.md left it open). Split a `command(ctx, text) *exec.Cmd` builder so the test asserts `filepath.Base(cmd.Path)=="pbcopy"`, `cmd.Args==["pbcopy"]`, and that reading `cmd.Stdin` yields the text — WITHOUT running pbcopy or touching the real clipboard. Ship a `Recording` fake (`Writes []string`, optional `Err`) for the TUI tests; `Last()` helper. The narrow interface is the DESIGN.md v1 boundary that lets OSC 52 drop in later.

### google-api-go (calendar/v3 + tasks/v1) read layer — testable shape (verified 2026-06-08, google.golang.org/api v0.283.0)

Built cal_agent's `internal/google`. Patterns that paid off, all unit-tested with zero real network/Keychain:
- **Inject the *http.Client, not OAuth.** Split the constructor: `NewClient(ctx, clientPath, account, store)` (prod: load oauth client + token + token source) → `newClientWithHTTP(ctx, account, *http.Client)` (the testable core). Tests build the service over `httptest.NewServer(...).Client()` and then override `svc.calendar.BasePath = srv.URL + "/"` / `svc.tasks.BasePath` to point list calls at the fake server. No OAuth in mapping/pagination tests.
- **Pagination is free**: `call.Pages(ctx, func(page) error {...})` follows `nextPageToken` itself — accumulate into a slice in the callback. Test it with a handler that branches on `r.URL.Query().Get("pageToken")` and asserts the token sequence (`["" "PAGE2"]`).
- **Token write-back on refresh**: wrap `oauth2.ReuseTokenSource(tok, cfg.TokenSource(ctx,tok))` in a tiny `persistingSource` whose `Token()` compares access-token+expiry against last-seen and calls `store.Set` only when it changed. Swallow the Set error (don't fail a valid request over a Keychain hiccup). Tested by seeding an expired token + a fake token endpoint and asserting the store now holds the fresh token; a "no write when still valid" test via a Set-counting store wrapper guards against Keychain churn.
- **Keep google-api types below the package boundary** — map to plain structs (`Event`, `BusyInterval`, `Task`) in separate `*_test`-friendly mapping funcs. Highest-value table tests: all-day `date` vs timed `dateTime` (+ `time.ParseInLocation` for date-only TZ), busy extraction excluding cancelled/transparent/zero-length, Tasks due date-only-midnight-UTC quirk (`time.Parse(RFC3339, "...T00:00:00.000Z")`).
- **410 Gone**: `errors.As(err, &*googleapi.Error)` then `.Code == 410`; wrap with a "sync token expired, full resync" message so the future incremental-sync layer has a clear signal. `googleapi.Error` survives `errors.As` through the wrap.
- **Live verification surface**: a `debug` scaffolding subcommand (`calendars`/`events`/`tasks`, shared `--email`/`--days`, runs all connected accounts when `--email` omitted) lets the user confirm live reads before any TUI exists. Never print tokens.

### OAuth2 installed-app loopback flow in Go — testable shape (verified 2026-06-08, golang.org/x/oauth2 v0.36.0)

Built cal_agent's `internal/auth`. Pattern that tested cleanly with zero network/browser/Keychain in unit tests:
- **Bind ephemeral port**: `net.Listen("tcp","127.0.0.1:0")`, derive `redirectURL = http://<addr>/callback`. Clone the `*oauth2.Config` per flow and set `RedirectURL` on the copy — never mutate the caller's config (it's shared/cached).
- **Auth URL**: `cfg.AuthCodeURL(state, oauth2.AccessTypeOffline, oauth2.ApprovalForce, oauth2.S256ChallengeOption(verifier))`. `verifier := oauth2.GenerateVerifier()`; `oauth2.AccessTypeOffline` → `access_type=offline` (refresh token), `oauth2.ApprovalForce` → `prompt=consent`. Exchange with `oauth2.VerifierOption(verifier)` for PKCE. These helpers exist in v0.36.0 — don't hand-roll PKCE.
- **Testability split that paid off**: make the callback handler its own type (`wantState`, `resultCh chan`) with `ServeHTTP` — unit-test it via `httptest.NewRecorder` for state-mismatch/error-param/code-captured WITHOUT spinning a server. Make `OpenBrowser func(string) error` and `LookupEmail func(...) (string,error)` injectable struct fields; full-flow test injects a fake browser that GETs the loopback callback in a goroutine and a fake token endpoint via `httptest.NewServer` (assert `code_verifier`/`code_challenge=S256` present there). No real `open`, network, or Keychain in any test.
- **Account email within read-only scopes**: with only `calendar.readonly`+`tasks.readonly` (no `openid email`), get the account email from `GET .../calendar/v3/calendars/primary` — its `id` IS the email. Avoids adding the calendar/v3 SDK dep to `auth`; a 30-line `net/http` call suffices.
- **macOS browser open** = `exec.Command("open", url).Start()` (don't Wait). Gate on `runtime.GOOS=="darwin"` and print the URL otherwise (v1 macOS-only boundary).

### go-keyring TokenStore: interface + memory fake, never touch real Keychain in tests (verified 2026-06-08, zalando/go-keyring v0.2.8)

`keyring.Get/Set/Delete(service, account)` store a string; JSON-encode the `*oauth2.Token` into it, service="cal_agent", account=email. Map `keyring.ErrNotFound` → a package `ErrTokenNotFound` sentinel on Get; treat it as success on Delete (idempotent). Put the macOS impl behind a `TokenStore` interface and ship an in-memory fake (`map[string]*oauth2.Token`, **return a copy** from Get so callers can't mutate stored state) — all unit tests run against the fake. `var _ TokenStore = NewKeychainStore()` compile-assert both impls.

### Day-granular window config beats raw durations for human editing (cal_agent, 2026-06-08)

Switched `window.back='720h0m0s'` → `back_days = 30`. Store as `int` days in TOML; expose `Back()/Forward() time.Duration` (×24h) and a `Resolve(now) (start,end)` method so in-memory math stays duration-based. If an env/flag override is still a duration string, quantize it to whole days at Merge time (round to nearest; positive sub-day rounds up to 1 so an explicit override never silently becomes 0). Far more readable in the file than `2160h0m0s`.

### go-toml/v2: nil-slice round-trip breaks reflect.DeepEqual; use omitempty (verified 2026-06-08, v2.3.1)

A `nil` slice field marshals to `key = []` and unmarshals back to a **non-nil empty slice**, so a `Defaults()`→Save→Load round-trip fails `reflect.DeepEqual` (prints identically, compares unequal). Fix is production-side, not a test hack: tag empty-by-default collection fields `toml:"name,omitempty"` so they are omitted from the file entirely — round-trips `nil`→absent→`nil` cleanly AND yields a cleaner human-editable config (no `accounts = []` noise). Alternative if you must keep the key: compare with `cmp.Diff(..., cmpopts.EquateEmpty())`. Prefer omitempty for config files.

### TOML duration pattern: wrap time.Duration with Marshal/UnmarshalText (verified 2026-06-08)

For human-editable duration config, define `type Duration time.Duration` with `MarshalText`/`UnmarshalText` (parse via `time.ParseDuration`). Renders as `'5m0s'`/`'720h0m0s'` in TOML, program holds a real `time.Duration` via a `.D()` accessor. `UnmarshalText` returning an error on a bad string gives free malformed-value rejection at Load time.

### Precedence chain implementation pattern (flags > env > file > defaults)

Clean, testable shape used in cal_agent: an `Overrides` struct of **pointer** fields (`*time.Duration`) where nil = "not set at this layer" (distinguishes absent flag from zero value); `FromEnv(getenv func(string) string)` returns Overrides (inject getenv for hermetic tests — no real env mutation); `Merge(Config, Overrides) Config` applies only non-nil fields; `Resolve(paths, env, flags)` layers LoadOrInit → Merge(env) → Merge(flags). Overrides stay in-memory — they do NOT persist to the file (test asserts on-disk file still holds defaults after a Resolve with overrides).

### First-run config: LoadOrInit sentinel pattern

`Load` returns `fs.ErrNotExist` unwrapped (via `errors.Is`) for a missing file so the caller distinguishes first-run from a parse error. `LoadOrInit(paths)` = Load; on ErrNotExist → EnsureDirs + Save(Defaults) + return defaults; second call reads the existing file untouched (test both branches). Save is atomic (temp file in same dir + rename), 0o600; dirs 0o700.

### Harness mode confirmed again (2026-06-08, cal_agent config increment)

This session again had **no subagent-dispatch tool** — deferred tools were only TaskCreate/Update/Get/List/Stop (a to-do list, not subagent spawn), RemoteTrigger, Cron, Push, EnterWorktree. `ToolSearch select:Agent,Task` returned nothing. Ran the go-code-writer ↔ go-test-engineer increment directly with Write/Edit/Bash, labelled as standing in for those agents, flagged in the report. Same fallback as documented. The persistent agents remain ready for a session where dispatch is available.

### XDG path resolution: relative XDG_CONFIG_HOME must be ignored

Per XDG spec a relative `XDG_CONFIG_HOME` is invalid → fall back to `~/.config`. Implement with `filepath.IsAbs(xdg)` (treats both empty and relative as "fall back" in one check). Keep path derivation pure (read env + UserHomeDir, no I/O); put the single MkdirAll in a separate `EnsureDirs` method so path logic is trivially table-testable with fabricated `Paths`.

### Bubble Tea v2 API gotchas (verified 2026-06-08, v2.0.7 / Go 1.25)

When scaffolding a Charm-v2 TUI, the v1→v2 breaks bite at compile time. Verified facts:

- **Module path moved to `charm.land`**, NOT `github.com/charmbracelet/...v2`. Use `charm.land/bubbletea/v2`, `charm.land/lipgloss/v2`, `charm.land/bubbles/v2`. `go get github.com/charmbracelet/bubbletea/v2` fails with "module declares its path as charm.land/bubbletea/v2".
- **`Model.Update` returns `(tea.Model, tea.Cmd)`** (was `(tea.Model, tea.Cmd)` with concrete in v1 examples) and **`View() tea.View`** — no longer returns `string`. Build the view with `tea.NewView("...")`.
- **Alt screen is a `View` struct field**, not a program option or command: `v := tea.NewView(s); v.AltScreen = true`. There is no `tea.WithAltScreen` and no `tea.EnterAltScreen` cmd in v2.
- **Key handling uses `tea.KeyPressMsg`** (type alias over `Key`) with `.String()` — not v1's `tea.KeyMsg`. Match `case tea.KeyPressMsg:`.
- `tea.Quit` and `tea.NewProgram(model, opts...)` / `p.Run()` are unchanged. A minimal compiling program: `Init() tea.Cmd` returning nil, the above `Update`/`View`. `go vet` clean.

### `google-calendar-api-expert` authored to fill the Google-API gap (2026-06-08)

The long-anticipated third-party-API gap was filled with `~/.claude/agents/google-calendar-api-expert.md` (+ seeded domain-knowledge file). Charter: Calendar API v3 + Tasks v1 + OAuth2 installed-app/loopback knowledge specialist; read-mostly (`tools: Read, Edit, Bash, WebFetch, WebSearch, Grep, Glob` — no Agent tool); `model: opus`. It hands `go-code-writer` a spec; it does not write production integration code. Reuse it for any future Google-Calendar/Tasks CLI.

### Harness gotcha: no subagent-dispatch tool in some sessions

In at least one session, neither an `Agent` nor a `Task`-dispatch tool was available (the `Task*` tools present are a to-do list, not subagent invocation), and no `subagent_type` could be spawned. When delegation to `architecture-advisor` / `go-code-writer` / `go-test-engineer` is impossible, the fallback is to run the research/work directly with the available primitives (`WebSearch`/`WebFetch` for an architecture pass), explicitly labelled as standing in for the named subagent, and flag it in the report. Do not silently skip the activity.

### Roster snapshot — activity → agent mapping (as of 2026-06-08)

Re-verify against `ls ~/.claude/agents/*.md` each run; the roster changes.

- **Architecture / library selection** → `architecture-advisor` (research-only; maintains a criteria checklist at `~/.claude/agents/architecture-advisor-criteria.md`).
- **Go implementation** → `go-code-writer` (small increments; CLI default `spf13/cobra` for multi-subcommand, stdlib `flag` for simple; avoids web frameworks; reads project `CLAUDE.md`).
- **Go tests** → `go-test-engineer` (table-driven, golden files, fakes, fuzz; never edits prod code).
- **GCP infrastructure (IaC)** → `gcloud-opentofu-architect` — **IaC/IAM/networking only.** Does NOT cover client-side API integration or OAuth installed-app flows. For an API-backed CLI this leaves a real gap.
- No agent currently covers **third-party-API client integration + OAuth user-auth flows** (Google Calendar API v3, Gmail, etc.). Expect to propose one (e.g. `google-api-go-expert` or a service-specific expert) on the first API-backed CLI.

### Same-session agent registration is not guaranteed

A subagent definition written during a session may not be invocable as a `subagent_type` until the harness reloads its agent registry. Standard handling: after authoring `<name>.md`, try invoking by `subagent_type`; if it isn't registered yet, fall back to the `general-purpose` agent with the new agent's charter + domain knowledge supplied inline, and tell the user the persistent agent is ready for future sessions (a reload picks it up).

### The Go agents are steered by the project `CLAUDE.md`

`go-code-writer` / `go-test-engineer` default to the user's Postgres-monitoring context but read a `CLAUDE.md` in the working directory. Always write/update the project `CLAUDE.md` (resolved stack, module path, directory layout, conventions, exit-code table) *before* delegating implementation, so they build the right thing.

### CLI interface-design checklist (Phase 0 intake)

Purpose & user · command surface (flat vs noun-verb vs verb-noun) · args vs flags (global/per-command, required/optional, defaults) · output (human default + `--json`/`--format`, `--quiet`/`--verbose`, `NO_COLOR`, TTY detection, exit codes) · input (stdin/piping, interactive vs `--yes`) · config (XDG `~/.config/<app>/`, env, flags; precedence flags > env > file > defaults) · auth/secrets (flow, token storage, refresh/revoke) · errors & help (actionable messages, `--help` examples, completion, `--version`) · distribution (static binary / `go install` / brew, version embedding, updates) · non-functional (offline, rate limits, retries/backoff, idempotency, `--dry-run`).

### House conventions for authoring a new agent

`~/.claude/agents/<name>.md` frontmatter: `name`, `description` (single line, `\n`-escaped, carrying *Invoke when* / *Do NOT* / *Examples*), `model: opus`, `color`. Body: `You are…` → domain facts → numbered `## Workflow` → `## Boundaries` → report format → `tighten-prose` word-economy pass. Pair it with a seeded `<name>-domain-knowledge.md`. Omit the `tools:` line to inherit all tools (needed for orchestrators that spawn subagents); add a restrictive `tools:` line for read-mostly research agents.

### freeslots engine: busy-inverse + per-day clip, DST via wall-clock time.Date (cal_agent, 2026-06-08)

Built cal_agent's `internal/freeslots` — the highest-value unit-test target per CLAUDE.md. Shape that tested cleanly (zero deps beyond stdlib + the project's own config/google types):
- **Public API the TUI consumes**: `Slot{Start,End}` (+`Duration()`), `DaySlots{Date,Weekday,Free}`, `Week{Monday, Days [7]DaySlots, Flat []Slot}`. `Compute(busy []google.BusyInterval, anchor, wh config.WorkingHours, minSlot time.Duration, loc) Week` — Monday-start, Days in Mon..Sun order, `Flat` is the chronological flat list for TUI index-select (same values as per-day Free). `WeekRange(now, offset int, loc) (mon, sun)` for arrow-key week nav. `FormatCopy(slots []Slot, loc) string` pure clipboard formatter.
- **Algorithm**: defensive `mergeBusy` (sort by start; coalesce when `!b.Start.After(last.End)` so overlapping AND touching merge; drop zero-length/inverted) → per day clip merged busy to `[winStart,winEnd)` → walk left-to-right emitting gaps → `addSlot` keeps gap iff `>= minSlot`. Non-working day (`!DayHours.IsWorkingDay()`) → nil. Boundary: `>=` means a gap exactly == minSlot is KEPT (test 30m==30m kept, 29m dropped, 31m kept).
- **DST without crashing**: build every window/clock boundary with `time.Date(y,mo,d,h,m,0,0,loc)` (via an `atClock` helper parsing "HH:MM"), NEVER offset math. Spring-forward Sunday 01:00–06:00 wall window → boundaries stay 1h/6h wall-clock but `Slot.Duration()` is 4h not 5h (the lost hour) — assert both. Berlin DST: spring 2026-03-29, fall 2026-10-25; spring-forward day is a weekend so force a Sun override to exercise it inside a window.
- **Week math**: Monday index = `(int(wd)+6)%7`; `today := time.Date(...0,0,0,0,loc)` then `AddDate(0,0,-wd+offset*7)`. AddDate (calendar days) crosses month/year boundaries and DST cleanly — test Jul→Jun back, Dec 2026→Jan 2027 forward.
- **Formatter golden**: group by `Start.Format("2006-01-02")`, prefix `Start.Format("Mon Jan 2")`, en-dash `–` (U+2013) between H:MM, comma-join ranges, append `Start.Zone()` abbrev per line, OMIT days with no slots. H:MM = no leading zero on hour, 2-digit minute (hand-rolled, NOT `Format("15:04")` which zero-pads the hour). Sort input first so an unordered multi-select still groups right. Empty selection → "". Golden via `-update` flag + `testdata/*.golden` (stdlib only; the repo had no prior golden convention though `charmbracelet/x/exp/golden` is an indirect dep).
- **Verify gotcha**: `gofmt -l .` failed the whole-module gate on TWO pre-existing files (`internal/auth/loopback.go`, `internal/config/resolve_test.go`) unrelated to the increment — scope-gate per package (`gofmt -l internal/freeslots/`) to avoid touching out-of-scope files; report the drift but don't fix it unasked.

### `calendars sync`/`list` scaffolding to populate config.Calendars before settings screen (cal_agent, 2026-06-08)

The free-slots loader (`internal/app`) scans only `visible=true` calendars, but `auth add` connects an account WITHOUT subscribing any calendars → empty `config.Calendars` → loader finds no busy → whole working window shows free. Bridged with a `calendars` scaffolding subcommand (sibling of `auth`/`debug`, all superseded later by the TUI settings screen), in `cmd_calendars.go` (`package main`):
- **The testable seam is a pure `mergeCalendars(existing []config.Calendar, account string, fetched []google.Calendar) (merged, added, updated, removed int)`** — no network. Rules: ID new to this account → append `Visible=true` (default ON so data shows immediately); existing same account+ID → update Summary/Color, **PRESERVE Visible** (never flip a user's hide), count `updated` only if Summary/Color actually changed; config calendar for THIS account absent from fetched → drop; **other accounts pass through untouched in original order**. Two-pass: walk existing (other accounts copy, this-account update-or-drop), then append new in fetched order. Copies by value into a fresh slice — added a no-mutation test.
- **Network/Keychain stay above the pure fn** behind a `calendarLister func(account)([]google.Calendar,error)`; prod closure builds `google.NewClient(...).ListCalendars`. `syncWithLister(paths,cfg,accounts,lister)` loops: a per-account fetch error is reported (with `errors.Is(err, google.ErrReauthorize)` → "run: cal_agent auth add") and SKIPPED — other accounts still sync; `config.Save` once at end iff something changed. Tested with a fake lister + `t.TempDir()` Paths (no real Keychain/network): one account succeeds, one errors → rc=1, succeeding account's merge still saved to disk.
- `calendars list` reads config only, groups by account, `[x]`/`[ ]` visible marks. Reused `selectAccounts` from cmd_debug.go (shared `--email`-or-all helper). gofmt note from the freeslots increment is now moot: `loopback.go`/`resolve_test.go` drift was since fixed, whole-module `gofmt -l .` clean this run.
- Harness again had no subagent-dispatch tool (only TaskCreate to-do list) — ran go-code-writer + go-test-engineer roles directly per the documented fallback. Small unblock; didn't run the orchestrator's full coverage-table ceremony.
