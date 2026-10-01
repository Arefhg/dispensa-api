# Dispensa — Project Brief & Roadmap to MVP

> *Dispensa* (Italian: "pantry") is a stock-management backend for small restaurants.
> Owner: Aref Haghgoorostami · Start: 28 September 2026 · MVP target: 13 December 2026

---

## 1. The problem

Small restaurants (trattorie, pizzerie, bars) usually track their stock on paper, in WhatsApp messages, or in the owner's head. The consequences are the same everywhere:

- Ingredients run out in the middle of service because nobody noticed they were low.
- Food is wasted or expires, and nobody knows how much money that costs.
- The owner can't answer simple questions: *How much did we spend at each supplier this month? What do we have in the storeroom right now?*

Big restaurant chains have expensive software for this. Small places don't.

## 2. The solution

Dispensa is a **backend API** that keeps an exact, trustworthy record of everything that enters and leaves a restaurant's storeroom.

A day with Dispensa:

1. **Morning.** A supplier delivers 20 kg of flour and 10 L of olive oil. A staff member records the delivery. Dispensa adds both items to stock and stores the price paid.
2. **During service.** The chef records that 3 kg of flour were used and 1 kg of tomatoes went bad. Dispensa subtracts them.
3. **Evening.** The owner opens the low-stock list and sees mozzarella is under its minimum level, so they order more.
4. **End of month.** The owner sees total spending per supplier and how much money was lost to waste.

**Who uses it:**

| Role | Can do |
|---|---|
| **Owner** | Everything: manage staff accounts, suppliers, ingredients; see all reports |
| **Staff** | Record deliveries, usage and waste; see current stock |

Every restaurant only ever sees its own data.

## 3. What "MVP" means here

**MVP (Minimum Viable Product)** is the smallest version that is genuinely usable and that you are proud to show.

For Dispensa, MVP = **`dispensa-api` v1.0**:

- It runs on your own server, on the public internet, with HTTPS.
- It has interactive API documentation where anyone can try every feature.
- Every feature is covered by automated tests that run on each push.

There is no visual interface yet. The frontend (`dispensa-web`) is the next phase, after MVP.

### In scope for MVP

- Accounts, login, and roles (owner / staff)
- Restaurants, with each restaurant's data isolated from the others
- Suppliers
- Ingredients, each with a unit (kg, L, pieces) and a minimum stock level
- Stock movements: delivery in, sale out, waste, manual correction (signed, append-only ledger)
- Deliveries with multiple lines (ingredient, quantity, unit price)
- Dishes and recipes: a dish links to ingredients via recipe lines
- Sales: recording dishes sold subtracts their recipe ingredients from stock
- Reports: current stock, low-stock list, dish availability, monthly spending per supplier, waste value

### Out of scope for MVP (later phases)

- Web interface → `dispensa-web` (December–January)
- Email or Telegram alerts
- Reading supplier invoices from a photo, demand forecasting → `dispensa-ai` (February–April)
- Payments, multiple languages, mobile app

## 4. How it works (architecture)

```
   Browser / API docs page
            │  HTTPS
            ▼
   ┌──────────────────┐
   │      Caddy       │  web server: handles HTTPS certificates automatically
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │   FastAPI app    │  your Python code: rules, validation, login
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │   PostgreSQL     │  the database: all data lives here
   └──────────────────┘

   All three run as Docker containers on one VPS (virtual server).
   GitHub Actions: runs tests on every push, deploys on every release.
```

### Tech stack

| Layer | Tool | Why this one |
|---|---|---|
| Language | Python 3.12 | The language of data and AI, so it carries into `dispensa-ai` |
| Web framework | FastAPI | Modern, fast, generates API docs automatically |
| Database | PostgreSQL 16 | The industry-standard relational database |
| Database access | SQLAlchemy 2 + Alembic | Python ↔ database mapping, and versioned schema changes |
| Validation | Pydantic 2 | Rejects bad input before it reaches the database |
| Auth | JWT tokens + Argon2 password hashing | Standard, secure login |
| Tests | pytest + httpx | Automated checks for every endpoint |
| Code quality | Ruff + mypy + pre-commit | Linting, formatting and type checking run automatically before every commit |
| Packaging | Docker + Docker Compose | Runs identically on your laptop and on the server |
| CI/CD | GitHub Actions | Tests on every push, deploy on every release |
| Monitoring | Structured logs + Sentry (free tier) | You know when something breaks, and why |
| Hosting | A small VPS (~€5/month) + domain (~€10/year) + Caddy | Your own real server with HTTPS |

## 5. Data model

```
restaurants ──< users              (a restaurant has many users; role = owner | staff)
restaurants ──< suppliers
restaurants ──< ingredients        (name, unit, category, min_stock)
restaurants ──< deliveries         (supplier, date, created_by)
deliveries  ──< delivery_lines     (ingredient, quantity, unit_price)
ingredients ──< stock_movements    (type, quantity, reason, created_by, created_at)
```

### The key design idea: the stock ledger

Dispensa **never stores "current quantity" as a number that gets edited.** Instead, every change is saved as a *movement*, like a bank statement:

| Date | Ingredient | Type | Quantity |
|---|---|---|---|
| 1 Oct | Flour | IN (delivery) | +20 kg |
| 1 Oct | Flour | OUT (usage) | −3 kg |
| 2 Oct | Flour | WASTE | −0.5 kg |

**Current stock = the sum of all movements = 16.5 kg.**

Why this matters: nothing is ever silently overwritten, every number can be explained ("who removed 3 kg, and when?"), and mistakes are fixed with a new correction movement, not by editing history. Banks and accounting systems work this way. It's a design decision worth explaining in interviews.

## 6. API endpoints (MVP)

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/auth/register` | anyone | Create restaurant + owner |
| POST | `/auth/login` | anyone | Get a token |
| GET | `/me` | logged in | Current user and restaurant |
| PATCH | `/restaurant` | owner | Edit restaurant profile |
| POST / GET | `/users` | owner | Add / list staff |
| PATCH | `/users/{id}` | owner | Edit or deactivate a user |
| CRUD | `/suppliers` | owner | Manage suppliers |
| GET | `/ingredients` | all | Owner: full list. Staff: names and units only (for waste) |
| POST / PATCH / DELETE | `/ingredients` | owner | Manage ingredients (archive, never delete with history) |
| GET | `/ingredients/{id}/movements` | owner | Full history of one ingredient |
| CRUD | `/dishes` | owner (write), all (read) | Dishes and their recipe lines |
| POST / GET | `/deliveries` | owner | Record / list deliveries |
| POST | `/sales` | all | Record dishes sold → sale movements |
| POST | `/waste` | all | Record waste |
| POST | `/corrections` | owner | Fix stock after a count |
| GET | `/reports/availability` | all | Portions possible per dish |
| GET | `/reports/stock` | owner | Current stock per ingredient |
| GET | `/reports/low-stock` | owner | Ingredients under minimum |
| GET | `/reports/spending?month=YYYY-MM` | owner | Spending per supplier |
| GET | `/reports/waste?month=YYYY-MM` | owner | Waste quantity and value |
| GET | `/health` | anyone | Liveness check |

## 7. Concepts you will learn

- **REST API:** a set of URLs that programs call to read or change data (`GET` reads, `POST` creates, `PATCH` edits, `DELETE` removes).
- **Relational database & SQL:** data stored in linked tables; SQL is the language to query them.
- **Migrations:** versioned, reversible changes to the database structure, stored in git like code.
- **Transactions:** a delivery with 5 lines is saved completely or not at all, never half.
- **Authentication vs. authorization:** *who are you* (login) vs. *what are you allowed to do* (roles).
- **Multi-tenancy:** many restaurants share one system but never see each other's data.
- **Automated testing:** code that checks your code, so you can change things without fear.
- **CI/CD:** GitHub runs the tests automatically, and deploys when you publish a release.
- **Containers:** packaging the app with everything it needs so it runs the same everywhere.
- **Linux server administration:** SSH, firewall, users, logs, HTTPS.

## 8. Working rules

1. **Claude Code writes the code; you stay the engineer.** You write the design doc, approve each approach, and review every change. **Nothing is merged until you can explain it.**
2. **One feature = one branch = one pull request.** Branch names like `feat/suppliers-crud`, `fix/negative-stock`.
3. **Commit messages** follow *Conventional Commits*: `feat: add supplier endpoints`, `test: cover low-stock report`, `fix: reject negative quantities`.
4. **Definition of done** for every feature: code works → tests written and passing → CI green → PR merged → README updated if needed.
5. **Commit at the end of every project session**, even if the work is small.
6. **Never commit secrets.** Real values go in `.env` (ignored by git); commit only `.env.example`.

## 9. Roadmap: 10 build weeks to MVP (11 calendar weeks — week 8 runs two weeks to absorb dishes/recipes/sales)

Weekly budget: ~10 h learning (mornings, 9:00–11:00) + ~11 h project (11:20–13:00, plus the extra afternoon blocks on Tuesday and Thursday).

### Week 1 — 28 Sep → 4 Oct · System design I: how a web system works

- **Learn (one topic per morning):**
  1. How a request travels: browser → DNS → TCP/TLS → server → response
  2. HTTP and REST API design: methods, status codes, resources, pagination, errors
  3. Servers: statelessness, reverse proxy, app server, workers
  4. Authentication vs. authorization: sessions vs. JWT, password hashing, roles
  5. Multi-tenancy: shared database with `restaurant_id` vs. schema or database per tenant
- **Build:**
  - [ ] GitHub profile: photo, bio, profile README; clean the iris repo
  - [x] Create `dispensa-api` repo with README, ROADMAP, CLAUDE.md
  - [ ] `docs/DESIGN.md` sections 1–4: requirements, architecture, API design, auth & tenancy
- **Done when:** you can draw Dispensa's architecture from memory and explain every arrow.

### Week 2 — 5 Oct → 11 Oct · System design II: data & operations

- **Learn:**
  6. Relational data modeling: entities, keys, relationships, normalization, constraints
  7. Transactions and ACID; concurrent writes; the ledger pattern
  8. Indexes and query performance; caching, and why Dispensa doesn't need it yet
  9. Background jobs and queues; scheduled tasks; idempotency
  10. Operating a system: deployment, backups, logs, monitoring, failure modes, how to scale step by step
- **Build:**
  - [ ] `docs/DESIGN.md` sections 5–9: data model, consistency, performance, jobs, operations & scaling, trade-offs
  - [ ] Design review with Claude Code; fix what it finds
  - [ ] Project skeleton: FastAPI "hello world", Ruff, mypy, pre-commit, `.gitignore`, `.env.example`; `/health` running locally
- **Done when:** the design doc is merged and `http://localhost:8000/docs` opens.

### Week 3 — 12 Oct → 18 Oct · Database

- **Learn:** SQL basics (SELECT, JOIN, GROUP BY), PostgreSQL, Docker basics.
- **Build:**
  - [ ] PostgreSQL in Docker Compose
  - [ ] SQLAlchemy models: `restaurants`, `ingredients`
  - [ ] First Alembic migration
  - [ ] Ingredients CRUD (create, list, read, update, delete)
- **Done when:** ingredients survive an app restart because they live in the database.
- *Exam review starts (30 min/day).*

### Week 4 — 19 Oct → 25 Oct · Exam block

- No project work. Study only.

### Week 5 — 26 Oct → 1 Nov · Tests & CI

- **Learn:** pytest, testing an API, GitHub Actions basics.
- **Build:**
  - [ ] Separate test database, pytest fixtures
  - [ ] Tests for every ingredients endpoint, including invalid input
  - [ ] Suppliers CRUD with tests
  - [ ] GitHub Actions: lint + type-check + tests on every push; CI badge in README
  - [ ] Test coverage report (target 80%+) with badge
  - [ ] Structured JSON logs with a request ID on every request
- **Done when:** a broken test turns the pull request red.

### Week 6 — 2 Nov → 8 Nov · Authentication & roles

- **Learn:** implementing what you designed in week 1: hashing, JWT, authorization.
- **Build:**
  - [ ] `users` model, register (creates restaurant + owner) and login
  - [ ] Protected endpoints; `/me`
  - [ ] Owner-only actions; owner can add staff
  - [ ] Every query filtered by the user's restaurant (tenant isolation)
  - [ ] Rate limiting on login (block brute-force attempts)
  - [ ] Tests: staff can't delete suppliers; restaurant A can't see restaurant B
- **Done when:** the isolation tests pass.

### Week 7 — 9 Nov → 15 Nov · Stock ledger, dishes & recipes

- **Learn:** database constraints, indexes, aggregate queries, row locking.
- **Build:**
  - [ ] `stock_movements` model and migration (signed quantity, per-type `CHECK`: delivery > 0, sale < 0, waste < 0, correction != 0)
  - [ ] `dishes` and `recipe_lines` models and migration; dishes CRUD (owner)
  - [ ] `POST /waste`; `POST /corrections` (takes counted quantity, computes delta, `SELECT ... FOR UPDATE`); reject impossible values
  - [ ] Current stock computed from movements
  - [ ] `/reports/stock` and `/reports/low-stock`
  - [ ] Ingredient history endpoint
  - [ ] Archive instead of delete for ingredients that have movements
- **Done when:** stock numbers are always explained by their movement history.

### Week 8 — 16 Nov → 29 Nov (two weeks) · Deliveries, sales & reports

- **Learn:** transactions in practice, pagination and filtering, API error design.
- **Build:**
  - [ ] Deliveries with multiple lines, saved in one transaction, creating delivery movements
  - [ ] `POST /sales`, multi-item, saved in one transaction, copies each dish's recipe into movements at sale time
  - [ ] `/reports/availability` (portions per dish, floored at 0)
  - [ ] Pagination and filters on list endpoints (by date, supplier, type)
  - [ ] `/reports/spending` and `/reports/waste` (month evaluated in the restaurant's timezone)
  - [ ] Consistent error responses
- **Done when:** a delivery or a sale with one invalid line saves nothing at all.

### Week 9 — 30 Nov → 6 Dec · Deploy to your server

- **Learn:** Linux server basics, SSH keys, firewalls, Docker in production, HTTPS.
- **Build:**
  - [ ] Production Dockerfile and compose file
  - [ ] Rent a VPS, buy a domain; SSH-key login only; firewall on
  - [ ] Caddy in front of the app with automatic HTTPS
  - [ ] First manual deploy: `https://api.<your-domain>/docs` is live
  - [ ] Error tracking with Sentry
  - [ ] Automatic daily database backups, and one restore actually tested
- **Done when:** a friend can open the API docs from their phone.

### Week 10 — 7 Dec → 13 Dec · Polish & release v1.0 (MVP)

- **Build:**
  - [ ] GitHub Actions deploy on every tagged release
  - [ ] Demo restaurant with realistic seed data and a public demo login
  - [ ] Final README: problem, live link, architecture diagram (from DESIGN.md), screenshots, how to run, how to test
  - [ ] Update DESIGN.md: what changed from the original design, and why
  - [ ] Tag `v1.0.0` and write release notes
  - [ ] Pin the repo; post it on LinkedIn
- **Done when:** every item in the checklist below is ticked.
- *If the December exam falls this week, this week moves after it.*

## 10. MVP checklist

- [ ] Live at a public HTTPS address
- [ ] All endpoints in section 6 work and are visible in `/docs`
- [ ] Roles and restaurant isolation enforced and tested
- [ ] Stock is always calculated from the ledger
- [ ] Tests pass in CI; badge is green; coverage 80%+
- [ ] Errors reported to Sentry; logs readable on the server
- [ ] Daily backups running, restore tested
- [ ] `docker compose up` runs the full project on a fresh machine
- [ ] No secrets in the repository
- [ ] README explains the project in under 2 minutes of reading
- [ ] Release `v1.0.0` published

## 11. After MVP

Each version = one tagged release with notes.

| Version | When | Feature |
|---|---|---|
| **v1.1** | late December – January | **E-invoice import:** owner uploads a supplier's FatturaPA XML invoice; deliveries are created automatically |
| v1.2 | January | **Suggested orders:** from low stock and past usage, a proposed order per supplier |
| v1.3 | February | **Alerts:** email/Telegram low-stock alerts sent by background workers (task queue) |

Then:

| When | Repository | Purpose |
|---|---|---|
| December–January | `dispensa-web` | React + TypeScript interface for the API |
| February–April | `dispensa-ai` | First AI-engineering project: till sales integration; paper receipt photos → delivery lines (suppliers without e-invoicing); demand forecasting; an assistant that answers questions about the restaurant's data |
