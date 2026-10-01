# Dispensa — Work Log

One entry per session, newest first. Written at the end of each session per CLAUDE.md §8.

---

## 2026-09-30

**Built**
- Installed WSL2 + Docker Desktop (guided through the elevated-terminal steps; Docker wasn't needed until this session)
- PR #7 `feat/database`: `docker-compose.yml` (PostgreSQL 16, named volume, healthcheck, port bound to `127.0.0.1` only), `app/config.py` (pydantic-settings), `app/db.py` (sync SQLAlchemy engine/session with a naming-convention `MetaData`), Alembic initialised (no models yet)
- PR #8 `feat/models`: `Restaurant`/`User`/`Ingredient` models (typed SQLAlchemy 2, `Mapped`/`mapped_column`), first migration generated, reviewed by hand, and fixed before applying; verified `upgrade head` → `downgrade base` → `upgrade head` all work
- PR #9 `feat/ingredients`: full ingredients CRUD (list/create/get/update/archive), `get_current_restaurant_id()` as the single tenant-scoping stub, a standard `{"error": {"code","message"}}` envelope for every error path, a real test-database setup (per-test transaction rollback), 11 tests; a follow-up fix sourcing `DEV_RESTAURANT_ID` from settings instead of a hardcoded constant, and refusing to run outside `ENVIRONMENT=development`

**Decisions**
- `role`/`unit` stored as `String` + `CHECK`, not a Postgres `ENUM` — simpler to extend later, no enum-alteration edge cases
- `ingredients.min_stock` defaults to `0` at the database level
- Composite `UNIQUE(restaurant_id, name)` on ingredients doubles as its `restaurant_id` index (leading-column btree) — no separate index needed there; `users.restaurant_id` still gets one
- Test schema is built by running the real `alembic upgrade head` against `dispensa_test`, not `Base.metadata.create_all()` — a broken migration should fail tests too
- `get_current_restaurant_id()` is the one explicitly-temporary place tenant identity comes from; it's wired to settings now so it can be swapped for real auth (week 6) without touching any router

**Learned**
- Alembic's autogenerate reliably captures CHECK constraints on a table's *first* migration (there's nothing to diff against), but is known to miss changes to them on later ALTER-style migrations — the "review it by hand" habit matters most once tables already exist
- SQLAlchemy naming-convention tokens: `%(column_0_name)s` (first column only) vs `%(column_0_N_name)s` (every column) — the difference between a composite unique constraint's name looking single-column or not
- `pre-commit`'s mypy hook runs in its own isolated environment, separate even from the project's `.venv` — its `additional_dependencies` list has to be kept in sync with whatever the code actually imports
- `ruff`'s `flake8-bugbear` (`B008`) flags `Depends(...)`/`Query(...)` in argument defaults by default — that's FastAPI's actual intended pattern, fixed via `extend-immutable-calls` config, not a `noqa`
- Filtering `(id, restaurant_id)` together in *one* query, not fetch-then-check, is what makes "wrong tenant" and "doesn't exist" both come back as the same plain 404

**Problems hit & how they were solved**
- `localhost` in `DATABASE_URL` resolved to IPv6 `::1` first on Windows, which isn't bound to anything — added ~90s to every single database command. Fixed by using `127.0.0.1` explicitly everywhere.
- A generated migration kept failing `ruff format --check` even after running `ruff format` — turned out an earlier command in the same `&&` chain had exited non-zero, so `ruff format` silently never ran. Not a code problem, a shell-chaining mistake.
- `mypy --strict` flagged `Settings()` as missing a required argument, because it couldn't see that `pydantic-settings` fills fields from the environment at runtime. Fixed by enabling the `pydantic.mypy` plugin, not by suppressing with `type: ignore`.

**Time spent:** not tracked live this session — fill in actual hours.

---

## 2026-09-29

**Built**
- PR #4 `docs/design`: added `docs/DESIGN.md` v1 (written by Aref); reviewed it and found one real bug (signed `stock_movements.quantity` vs. a `CHECK` that only allowed positive values) plus four ambiguities (correction semantics, report-month timezone, availability flooring, waste vs. negative stock) — all resolved and applied; updated `ROADMAP.md` to move recipes & sales into the MVP (weeks 7–8) and push the MVP date to 13 December; synced `ROADMAP.md`'s endpoint table to match `DESIGN.md`
- PR #5 `feat/skeleton`: Python 3.12 venv, `pyproject.toml` (FastAPI, uvicorn, pytest, ruff, mypy), `app/main.py` with `GET /health`, one test, README run instructions
- PR #6 `chore/pre-commit`: `.pre-commit-config.yaml` (ruff-check, ruff-format, mypy via astral-sh/ruff-pre-commit + pre-commit/mirrors-mypy), installed the hook, proved it actually blocks a bad commit (deliberately added an unused import, watched it get refused)

**Decisions**
- `stock_movements.quantity` stays signed; `CHECK` written per movement type (`delivery > 0`, `sale < 0`, `waste < 0`, `correction != 0`) instead of one blanket `> 0` check
- Corrections store a server-computed delta (`counted - current_stock`) from a counted absolute quantity, with a row lock (`SELECT ... FOR UPDATE`) to avoid races between concurrent counts
- Sync SQLAlchemy chosen over async — simpler, sufficient at Dispensa's target scale (~100 restaurants)
- `mypy` set to `strict = true` from the very first file, not relaxed-then-tightened later

**Learned**
- Why a design review happens *before* code: the signed-quantity bug was caught while it was still a paragraph in a markdown file, not a migration already applied to a database
- Pre-commit hooks run in their own isolated environment, not the project's `.venv` — why `additional_dependencies` exists for mypy to resolve `fastapi`/`httpx` types
- `rev:` in `.pre-commit-config.yaml` and the matching package's version pin in `pyproject.toml` are two independent knobs on the same tool — they have to move together or local/hook behavior can drift apart

**Problems hit & how they were solved**
- Thought PR #4 and #5 were merged on GitHub (reported as merged), but `gh pr list` and `origin/main`'s own log showed them still open — flagged the discrepancy instead of proceeding, held off deleting any branches, and re-verified before continuing once actually confirmed merged.

**Time spent:** not tracked live this session — fill in actual hours.

---

## 2026-09-28

**Built**
- Checked the environment: git 2.55.0, gh 2.101.0 (logged in), Python 3.14.5 default with 3.12 also available via `py -3.12`; WSL2 not installed — deferred rather than derailing this session
- Initialized git, added an MIT `LICENSE`, created the public GitHub repo `dispensa-api`, pushed the initial scaffold (`README.md`, `ROADMAP.md`, `CLAUDE.md`, `docs/DESIGN.md` skeleton)
- Created week-1 GitHub issues: #1 GitHub profile cleanup, #2 repo scaffold (closed the same session — done as part of the scaffold work), #3 `docs/DESIGN.md` sections 1–4
- Started `docs/DESIGN.md` §1 (Requirements) as a review conversation — Claude asked questions about users and their workflows, Aref writes the actual doc
- Created a separate public repo `Arefhg/Arefhg` with a GitHub profile README

**Decisions**
- Deferred WSL2/Docker Desktop install to its own session rather than doing it mid-task — flagged as a week-1 to-do instead

**Learned**
- The working split for this whole project: Claude writes the code, Aref designs/decides/reviews, and nothing is considered done until Aref can explain it
- Why `.claude/settings.local.json` doesn't belong in a public repo even though it holds no secrets — it's local tool config, not project code

**Problems hit & how they were solved**
- `git commit` failed with "Author identity unknown" on the very first commit — fixed by setting `git config --global user.name`/`user.email` once, which then applied to every repo going forward.

**Time spent:** not tracked live this session — fill in actual hours.
