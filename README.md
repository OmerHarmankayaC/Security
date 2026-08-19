# Shift Scheduling Decision Support Tool

A constraint-programming (Google OR-Tools CP-SAT) decision support tool for
building shift schedules: it assigns staff to hourly demand under hard rules
(rest periods, weekly caps, competencies) while balancing night hours,
weekend hours and total load fairly. A web application built on FastAPI +
React + PostgreSQL.

Written as an internship project. The rules, demand patterns and staffing
figures in this repository are illustrative — the tool is generic, and the
data it ships with is generated.

For scope, architecture, and the rule catalogue, see the four canonical
documents under [`docs/`](docs/) (Charter, SRS, Backlog, SDD).

The development plan lives in two files: the active plan
[`docs/turlar/UYGULAMA_PLANI_V2.md`](docs/turlar/UYGULAMA_PLANI_V2.md) (phase
two, run in tours), and the closed daily plan for phase one,
[`docs/turlar/UYGULAMA_PLANI.md`](docs/turlar/UYGULAMA_PLANI.md). Progress
tracking is likewise split: the active log is
[`PROGRESS_V2.md`](PROGRESS_V2.md), the archive is [`PROGRESS.md`](PROGRESS.md).

## Screenshots

The day grid, where demand and assignments are read hour by hour:

![Day grid](docs/gorseller/gun-izgarasi.png)

The solve screen — the run is startable, watchable, and stoppable; a stopped
run offers the best schedule found so far rather than discarding it:

![Solve screen](docs/gorseller/cozum-ekrani.png)

The analysis screen, where a published version is measured — coverage, quota
status, fairness distributions, and the penalty breakdown:

![Analysis screen](docs/gorseller/analiz-ekrani.png)

## Status

Six acceptance criteria are defined in the Project Charter (section 5).
**Five of six pass.**

| Criterion | Threshold | Measured (demo server) | Result |
|---|---|---|---|
| K1 — time to a usable schedule | < 60 s | 23.88 s | ✅ |
| K2 — hard constraint violations | 0 | 0 | ✅ |
| K3 — night fairness | at most 10% of staff deviate > 8 night hours | 33 of 40 (82.5%) | ❌ |
| K4 — infeasible instance is explained | ≥ 1 gap, fully described | 151 intervals | ✅ |
| K5 — manual edit validation | < 1 s | 0.251 s | ✅ |
| K6 — re-solve difference reported | report produced | 896 changes | ✅ |

**K3 does not pass, and the reason is search time rather than staffing.** The
reachability diagnostic confirms every pool can reach its target: the
obstacle is that the search does not get there within the time limit. On the
reference instance, moving from 60 to 300 seconds took the number of people
outside their fair share from 10 of 40 down to 1 of 40, while re-tuning the
soft-constraint weights only moved the maximum deviation from 25.0 to 22.0.

That distinction matters and is easy to misread: **most of the improvement in
night fairness comes from the longer search, not from weight calibration.**
Presenting it as a calibration result would be misleading.

Two changes followed from this and are not yet reflected in the numbers
above: the criterion was redefined as a distribution (previously "no single
person deviates more than 8 hours", which turned on one person and was
extremely sensitive to where the search happened to stop), and the solver
time limit was raised from 60 to 300 seconds. **The table still shows the
measurement taken under the previous definition and the previous limit; it
will be re-measured on the demo server.**

## Known limitations

- **The solver returns the best schedule found within its time limit**, not a
  proven optimum. A longer limit generally produces a fairer schedule; the
  limit is a parameter (`cozucu_zaman_limiti_saniye`, default 300 s).
- **Cumulative fairness looks back 90 days** (a rolling window over published
  versions). Deviation accumulated before that window is not visible to the
  system, and a deviation accumulated over previous periods cannot be closed
  within a single period.
- **A published schedule is read-only.** Corrections are made by deriving a
  new draft and publishing it; the previous version is archived rather than
  overwritten, so employees can always be shown what changed.
- **Single facility.** Buildings and duty points belong to one facility;
  separate personnel pools per facility are not modelled.
- **Availability has day-level resolution** (full day / morning / afternoon),
  not arbitrary hour ranges.
- **One scheduler at a time.** Concurrent editing of the same version by two
  managers is not handled.

## Measurement environment

The numbers above were measured on the demo server, not the development
machine — that is the binding environment.

| | Development machine | Demo server (reference) |
|---|---|---|
| OS | macOS 15.7.3, arm64 | Linux x86_64 (Ubuntu) |
| Cores | 10 | 4 |
| Memory | 16 GB | 7 GB |
| Search workers | 3 | 3 (cores − 1) |

**The demo server is shared** — other services run on the same machine — so
the measured times should be read as an upper bound rather than a best case.
CP-SAT is also non-deterministic under parallel search: the same instance can
yield different (equally good) solutions across runs. K3's deviation and K4's
gap count vary between runs; the pass/fail decisions and the K1/K2/K5 values
do not.

## Requirements

See [`VERSIONS.md`](VERSIONS.md) for pinned versions. Summary:

- Python 3.12+
- Node.js 22.x
- PostgreSQL 16 (running locally; `.env` must point at this server)

## Setup

```bash
cp .env.example .env   # edit values as needed
./scripts/kurulum.sh
```

The script sets up the backend virtual environment, applies database
migrations, runs the backend tests/lint checks, and installs frontend
dependencies.

## Development

Backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

`http://localhost:8000/health` should return 200.

Solver worker (**runs in a separate terminal, alongside the API**):

```bash
cd backend
source .venv/bin/activate
python scripts/cozum_iscisi.py
```

The solve job runs in a separate service, not in the API process (SDD 3.4.4);
the two processes only communicate through the database. If this worker
isn't running, solve requests sit `queued` and no schedule is ever produced.
Development thus follows the same path as production.

Creating the first admin account (SRS FR-10.10 — there is **no** in-app
sign-up endpoint; this is how the account-less system bootstraps its first
account):

```bash
cd backend && source .venv/bin/activate
python scripts/yonetim_hesabi_olustur.py
```

The password cannot be passed as an argument; the script prompts for it
without echoing (a password typed on the command line would end up in shell
history and `ps` output). Subsequent accounts are created from the Users
screen in the UI.

**In local development, set `OTURUM_CEREZI_SECURE=false` in `.env`.** The
session cookie carries the `Secure` attribute in production, and the browser
won't send it back over plain `http://localhost`; login fails silently if this
isn't disabled.

Demo data for presentations (FR-1.14 — the security-personnel scenario from
SRS 3.3). Periods are anchored **to the day they're generated**, and
schedules are produced by the **real solver** — the data isn't pinned to
fixed dates:

| Period | Location | Status | What it shows |
|---|---|---|---|
| Last | previous week | published | Past schedule; the warm-start window for the next one (TD-5) |
| This Week | **includes today** | archived + published | Balanced period. Powers "My Shifts" and "next shift" on the employee panel; two versions exist so the "changed days" marker also works (FR-9.4) |
| Tight | next 4 weeks | solved | An unclosable coverage gap (Backlog B-14). The conflict is built through **availability**: five of the shift-supervisor pool are on leave and no one else can fill that slot (H8) — independent of block length |
| Holiday | first national holiday week | unpublished | An official holiday drops staffing (FR-1.10, TD-3); the only period with an **open preference window** |
| Overtime | one week after the holiday | solved | A third of the security pool is on leave; the remaining staff's weekly load crosses the threshold (45h) and **quota consumption becomes visible** (H10) |
| Quota Limit | the week after that | solved | Staff with a high carry-over balance. Anyone at their quota keeps working up to the threshold and no further; the pre-check flags this as a warning |

Also included: 30 staff members (3 fixed-shift, 1 deactivated), a two-year
official holiday calendar, all four availability types, half-day slots
(TD-4), and all three preference states.

**Staffing is sized to match demand** (SRS 3.3.6): at 30 people, the weekly
load per person is 38.4 hours — close to but under the overtime threshold.
At the previous staffing level of 44, load drops to 26 hours, no one
approaches the threshold, and H10 never triggers; demo data that can't show
the rules working amounts to the same thing as the rules not being written.

```bash
cd backend && source .venv/bin/activate
python scripts/demo_veri_uret.py           # first run
python scripts/demo_veri_uret.py --reset   # wipe and regenerate existing demo data
python scripts/demo_veri_uret.py --reset --cozme   # definitions only, skip solving
```

Solving takes several tens of seconds; skip it with `--cozme` if you only
need to look at the definition screens.

## Login

There is no sign-up screen (FR-10.1); the first account is created out of
band via a script (FR-10.10). The default username is **`admin`**, with the
admin role — the only role that can manage user accounts:

```bash
cd backend && source .venv/bin/activate
python scripts/yonetim_hesabi_olustur.py
```

The password can't be passed as an argument; the script prompts for it twice
without echoing (minimum 12 characters). Subsequent accounts are created from
the Users screen in the UI.

The test suite never touches this account: tests run against a separate
database (see "Tests and Lint").

Frontend:

```bash
cd frontend
npm run dev
```

## Tests and Lint

**Tests run against a SEPARATE database** (Product Backlog B-20). The suite
refuses to run if it doesn't see a test database in the connection string —
it fails loudly instead of silently wiping development data.

One-time initial setup:

```bash
createdb vardiya_test
cd backend
VERITABANI_URL=postgresql+psycopg://vardiya:<PASSWORD>@localhost:5432/vardiya_test \
  .venv/bin/alembic upgrade head
```

Set the address in `backend/.env` (see the line in `.env.example`):

```
TEST_VERITABANI_URL=postgresql+psycopg://vardiya:<PASSWORD>@localhost:5432/vardiya_test
```

The database name must contain `test`; the guard looks for it. The schema is
built through migrations, not `create_all` — the test database follows the
same migration chain as the development database, so the migrations
themselves are implicitly exercised on every run. A new migration must be
applied to both.

```bash
cd backend && source .venv/bin/activate
ruff check . && ruff format --check .
python -m pytest -q
```

```bash
cd frontend
npx tsc --noEmit -p tsconfig.app.json
```

## Project Structure

```
backend/    FastAPI application, SQLAlchemy models, Alembic migrations
frontend/   Vite + React + TypeScript (strict mode)
docs/       Charter, SRS, Backlog, SDD (the canonical four)
docs/turlar/ Plans, tour prompts, handover notes — a record, NOT a source of truth
scripts/    Setup and utility scripts
```

## Progress Tracking

Cross-session context is kept in [`PROGRESS_V2.md`](PROGRESS_V2.md); the
phase-one log in [`PROGRESS.md`](PROGRESS.md) is closed and archival only.

## License

**No licence is granted.** This repository is published for code review as
part of an internship project; all rights are reserved by default. You are
welcome to read the code. If you want to use, modify, or redistribute any
part of it, please get in touch first.
