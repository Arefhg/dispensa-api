# Dispensa API

> Stock management for small restaurants: every delivery, usage and waste recorded in a ledger, so the owner always knows what's in the storeroom and what it costs.

🚧 **Status:** in development — MVP (v1.0) planned for end of November 2026. See the [roadmap](ROADMAP.md).

## The problem

Small restaurants track stock on paper or in their heads. Ingredients run out mid-service, food is wasted without anyone measuring it, and owners can't answer simple questions like *"how much did we spend at each supplier this month?"*

## What Dispensa does

- **Deliveries in, usage and waste out:** every change is recorded as a movement.
- **Current stock** calculated from the movement history, never edited by hand.
- **Low-stock list:** ingredients under their minimum level.
- **Reports:** spending per supplier, waste per month.
- **Roles:** owners manage everything, staff record daily work; each restaurant sees only its own data.

## Key design decision: a stock ledger

Stock is never stored as an editable number. Like a bank statement, every change is an immutable movement, and current stock is their sum. Every number can be traced to who changed it and when, and mistakes are fixed with a correction, not by rewriting history.

## Tech stack

Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2 + Alembic · Pydantic 2 · JWT auth · pytest · Ruff + mypy · Docker Compose · GitHub Actions · Caddy (HTTPS)

## Architecture

```
Client ──HTTPS──▶ Caddy ──▶ FastAPI app ──▶ PostgreSQL
                   (all running in Docker on a VPS)
```

## Run locally

Requires Python 3.12.

```bash
py -3.12 -m venv .venv
.venv/Scripts/activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install

uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive API docs.

Run checks:

```bash
pytest
ruff check .
ruff format --check .
mypy app tests
```

## License

MIT
