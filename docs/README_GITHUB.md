# VARDİS — Shift Scheduling Decision Support System

A web-based decision support tool that builds security-staff work schedules under
hard legal and ergonomic constraints while balancing workload fairly across the
team. Built with Google OR-Tools CP-SAT, FastAPI and React.

**Live demo:** [vardiya.omerharmankaya.com](https://vardiya.omerharmankaya.com)
(sign-in required)

---

## What makes it a decision support tool, not a scheduler

Two design choices separate this from a constraint-solving exercise:

**1. It never says "infeasible."** When staffing is short, the system still
produces a schedule and shows *where* the gap is — which day, which hours, which
post, how many people missing. Coverage is a heavily weighted soft objective, not
a hard constraint, precisely so that an under-staffed period yields a usable
schedule plus a diagnosis instead of an error message.

**2. Manual edits are validated live.** A supervisor can change any assignment;
the system reports which rule broke, immediately, using the *same rule
implementation* that built the model. A rule is never coded twice — one class
both adds the CP-SAT constraint and validates a manual edit, and a
solver–validator agreement test over randomized instances keeps the two honest.

The system supports the person making the decision; it does not take the decision
away.

---

## Scheduling model

Work time is decided **at the hour level**. There is no shift-type catalogue: the
solver decides when each person starts and how long they work.

```
z[p,s] ∈ {0,1}     person p works at absolute hour s
x[p,s,n] ∈ {0,1}   … at post n
```

The time axis is absolute across the planning period rather than resetting each
day — otherwise a block crossing midnight would be counted as two separate
blocks and the continuity rule would forbid exactly the night shifts it should
allow.

### Rule catalogue

**Hard constraints** — never violated:

| | |
|---|---|
| H1 | One continuous block per day, minimum length, fixed post throughout |
| H2 | Minimum rest between consecutive blocks |
| H3 | Maximum consecutive night days |
| H4 | Maximum consecutive working days |
| H5 | Absolute weekly hour ceiling (rolling seven-day window) |
| H6 | At least one full day off per week |
| H7 | Availability (leave, sick days) |
| H8 | Post prerequisite competency |
| H9 | Maximum daily hours |
| H10 | Annual overtime quota — hours above the weekly threshold, summed over calendar weeks |

**Soft objectives** — weighted penalties the solver minimizes:

| | |
|---|---|
| S1 | Coverage (dominant weight; under- and over-staffing both penalized) |
| S2 | Night-hour fairness |
| S3 | Weekend-hour fairness |
| S4 | Total-hour balance |
| S5 | Honoring approved preferences |
| S6 | Consistency of start times across consecutive days |
| S7 | Avoiding isolated single working days |
| S8 | Minimizing change from the previous published version |

Fairness targets are **per-person fair shares**, not a pool average: each unit of
demand is divided among those who can actually reach that post. A team member who
can only work one post is measured against what they can actually take on — a
single average would mark them permanently short of a target they can never
reach.

Two different notions of "week" coexist deliberately: rolling seven-day windows
for rest rules, and discrete calendar weeks for the overtime quota. A quota is a
sum, and a sum is only meaningful over non-overlapping windows.

---

## Architecture

```
React + TypeScript          ← admin console and employee panel
        │  HTTPS / JSON
FastAPI + SQLAlchemy        ← REST API, authentication, rule catalogue
        │  PostgreSQL only
Solver worker (separate)    ← OR-Tools CP-SAT, 3 search workers
```

The solver runs as a **separate systemd service**. Solving a real period takes
longer than an HTTP request should, so jobs are queued and polled. The two
processes communicate **only through the database** — no message broker, no
shared memory. A running job survives page navigation, browser refresh, and
sign-in from another device, because the job's identity lives in the database
rather than in the client.

Stopping a running solve does not discard the result: the search ends, the best
solution found so far is held, and the user chooses to use it, discard it, or
continue searching from it.

### Stack

- **Backend** — Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Solver** — Google OR-Tools CP-SAT
- **Frontend** — React, TypeScript, Vite, Tailwind
- **Auth** — Argon2id password hashing, database-backed sessions (revocable),
  three roles
- **Deployment** — systemd services behind Caddy; no Docker

---

## Documentation

The project is specified before it is built. Four documents are the single source
of truth and every design decision — including reversed ones — is recorded with
its rationale in the backlog's decision log.

| Document | Contents |
|---|---|
| Project Charter | Scope, acceptance criteria, risks |
| SRS | Requirements, rule catalogue, design decisions (TD-*) |
| SDD | Architecture, data dictionary, algorithms, screen catalogue |
| Product Backlog | Deferred items, technical debt, decision log |

Acceptance criteria are measured, not asserted: a script re-runs them and the
performance note reports the numbers from that run.

---

## Local setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
alembic upgrade head
python scripts/yonetim_hesabi_olustur.py     # first admin account
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Requires PostgreSQL 15+ and Python 3.13+. Tests run against a **separate
database**; the suite refuses to start if the connection string does not point at
one.

---

## Status

Actively developed. The system is deployed and running; the current work is a
migration from fixed shift types to hour-level scheduling.

The codebase and documentation are in Turkish, since the tool is built for a
Turkish-speaking operations team.

---

## Note on data

All personnel records, demand figures and staffing numbers in this repository are
**synthetic demonstration data** generated by `scripts/demo_veri_uret.py`. They do
not reflect any real organization's staffing or security arrangements.
