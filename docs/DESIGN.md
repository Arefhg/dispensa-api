# Dispensa — Design Document

> Status: v1 draft · Author: Aref · Date: 29 September 2026
> Scope: `dispensa-api` v1.0.0 (MVP)

---

## 1. Requirements

### 1.1 Problem
Small restaurants track stock on paper or in their heads. They run out of ingredients mid-service, lose money to waste, and can't answer "what do we have?" or "what did we spend?".

### 1.2 Users and what they do

**Giulia — owner of a small pizzeria.**
- Sets up the restaurant: registers it, adds ingredients, suppliers and dishes with their recipes.
- Adds staff accounts; deactivates them when someone leaves.
- Records deliveries from suppliers (she handles invoices). She may record a delivery later than it arrived, so a delivery has its own `delivered_on` date.
- Sees ingredient stock, low-stock list, spending per supplier and waste value.
- Does a stock count now and then and fixes differences with a correction.

**Marco — pizza chef (staff).**
- Records sales during or after service: "3 margherita, 1 carbonara". Dispensa removes the ingredients from stock using each dish's recipe.
- Records waste (e.g. 1 kg of tomatoes went bad).
- Sees **how many portions of each dish can still be made** ("margherita: 12, carbonara: 2").
- Does **not** see ingredient quantities, prices, spending, or other staff accounts.

### 1.3 Functional requirements (MVP)
1. A restaurant owner can register a restaurant and their own account.
2. The owner manages staff accounts (add, list, deactivate).
3. The owner manages suppliers, ingredients, dishes and recipes.
4. The owner records deliveries (multiple lines, with prices).
5. Staff and owner record sales; stock goes down by the recipe.
6. Staff and owner record waste.
7. The owner records corrections after a physical count.
8. Staff see portions available per dish; the owner also sees ingredient stock and reports.
9. Every restaurant sees only its own data.

### 1.4 Non-functional requirements
- **Correctness:** every stock number is explainable from its history.
- **Isolation:** no request can ever read or change another restaurant's data.
- **Security:** hashed passwords, HTTPS only, brute-force protection on login.
- **Availability:** a single server is fine; daily backups with a tested restore.
- **Scale target:** up to ~100 restaurants, a few thousand movements per restaurant per month.

### 1.5 Out of scope for v1.0
Web interface, PDF/file uploads (e.g. invoices), alerts, suggested orders, multiple languages, payments, AI features.

---

## 2. Architecture

```
Client (browser / API docs)
        │ HTTPS
        ▼
Caddy (reverse proxy, automatic TLS)
        │ HTTP (internal)
        ▼
FastAPI app (stateless; validation, auth, business rules)
        │ SQL
        ▼
PostgreSQL 16 (single source of truth)
```

- All three run as Docker containers on one VPS.
- The app is **stateless**: all state is in Postgres, the login token carries identity. This means the app can be restarted or copied to a second server without losing anything.
- CI (GitHub Actions) runs lint, type-check and tests on every push; a tagged release deploys.

---

## 3. API design

Conventions:
- JSON over HTTPS. Resources are plural nouns (`/ingredients`).
- `POST` creates (201), `GET` reads (200), `PATCH` edits (200), `DELETE` archives (204).
- Errors use one shape: `{"error": {"code": "...", "message": "..."}}`. Status codes: 400/422 bad input, 401 not logged in, 403 not allowed, 404 not found **or belongs to another restaurant**, 409 conflict.
- Lists are paginated: `?limit=50&offset=0`.
- Quantities are decimals in the ingredient's unit; money is in EUR with 2 decimals.

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

Example — record a sale:
```json
POST /sales
{ "sold_at": "2026-11-12T20:30:00+01:00",
  "items": [ {"dish_id": 3, "quantity": 2}, {"dish_id": 7, "quantity": 1} ] }
```

---

## 4. Authentication, authorization and multi-tenancy

**Authentication (who are you?)**
- Passwords hashed with Argon2. Never stored or logged in plain text.
- Login returns a JWT access token valid for 8 hours (one shift). No refresh tokens in v1.0 — the user logs in again.
- The token contains `user_id`, `restaurant_id`, `role`.
- On every request the app loads the user from the database and rejects inactive users. So deactivating a staff member works **immediately**, not when their token expires.
- Login is rate-limited (e.g. 5 failed attempts per email per 15 minutes).

**Authorization (what can you do?)**
- Two roles: `owner`, `staff`. Checked by a FastAPI dependency on each endpoint (`require_owner`).
- A restaurant always has at least one active owner; the last owner can't be deactivated.

**Multi-tenancy (whose data?)**
- One shared database. Every tenant table has a `restaurant_id` column.
- `restaurant_id` is **always taken from the token, never from the request body or URL**.
- Every query filters by it through one shared helper, so it can't be forgotten.
- Asking for another restaurant's object returns **404**, not 403, so nobody can learn which IDs exist.
- Tests: restaurant A tries to read and change every kind of object of restaurant B and must fail.
- Why not a database per restaurant: much more complex to run and migrate; not needed at this scale.

---

## 5. Data model

```
restaurants ─< users
restaurants ─< suppliers
restaurants ─< ingredients ─< stock_movements
restaurants ─< dishes ─< recipe_lines >─ ingredients
restaurants ─< deliveries ─< delivery_lines >─ ingredients
restaurants ─< sales ─< sale_items >─ dishes
```

| Table | Main columns |
|---|---|
| restaurants | id, name, address, vat_number (optional), timezone (default Europe/Rome), created_at |
| users | id, restaurant_id, email (unique), full_name, password_hash, role, is_active, created_at |
| suppliers | id, restaurant_id, name, phone, email, archived_at |
| ingredients | id, restaurant_id, name, unit (`kg`/`l`/`pcs`), min_stock, archived_at |
| dishes | id, restaurant_id, name, archived_at |
| recipe_lines | id, dish_id, ingredient_id, quantity_per_portion |
| deliveries | id, restaurant_id, supplier_id, delivered_on, created_by, created_at |
| delivery_lines | id, delivery_id, ingredient_id, quantity, unit_price |
| sales | id, restaurant_id, sold_at, created_by, created_at |
| sale_items | id, sale_id, dish_id, quantity |
| stock_movements | id, restaurant_id, ingredient_id, type, quantity (signed), unit_cost, reason, source_type, source_id, created_by, created_at |

Constraints:
- Names unique per restaurant: `UNIQUE (restaurant_id, name)`.
- Quantities and prices `> 0` (`CHECK`), except correction movements, which can be negative.
- Movement `type` ∈ `delivery`, `sale`, `waste`, `correction`.
- Quantities `NUMERIC(12,3)`, money `NUMERIC(10,2)`. Never floats for money.

---

## 6. The stock ledger and consistency

- Stock is **never stored as an editable number**. Current stock of an ingredient = `SUM(quantity)` of its movements.
- Movements are **append-only**: no UPDATE, no DELETE. A mistake is fixed with a new `correction` movement.
- Each movement links back to what caused it (`source_type`, `source_id`: a delivery, a sale, or nothing for waste/corrections).
- **A sale copies the recipe at the moment of sale** into movements. If the recipe changes later, past stock numbers don't change.
- **Transactions:** a delivery with all its lines, or a sale with all its items, is saved in one database transaction — all or nothing.
- **Negative stock is allowed, and flagged.** If a sale would take stock below zero, the sale is still saved (the pizza was really sold; refusing it would make the data lie). The report shows the negative number, which tells the owner a delivery or count is missing.
- **Availability** = for each dish, the minimum over its recipe lines of `floor(stock / quantity_per_portion)`. Computed when asked, not stored.
- **Waste value** uses the last delivery price of that ingredient (stored as `unit_cost` on the movement when it is created).

---

## 7. Performance

- Index `stock_movements (restaurant_id, ingredient_id, created_at)` — covers stock sums and history.
- Indexes on every `restaurant_id` foreign key.
- At the target scale, summing movements on every request is fast enough. **No cache, no stored balances in v1.0.** If it becomes slow: add a monthly snapshot table, measured first.

---

## 8. Background jobs

None in v1.0. Everything happens inside the request. Alerts (v1.3) will introduce a job queue.

---

## 9. Operations

- Deploy: Docker Compose on one VPS; Caddy handles HTTPS.
- Config and secrets via environment variables; `.env` never committed.
- Structured JSON logs with a request ID; errors to Sentry.
- Daily `pg_dump` backup copied off the server; one restore tested before v1.0.
- Scaling path, only when needed: bigger VPS → separate DB server → second app instance behind Caddy.

---

## 10. Decisions and trade-offs

| Decision | Why | Cost |
|---|---|---|
| Ledger instead of stored stock | Every number is explainable; no silent overwrites | Sums on read; needs good indexes |
| Recipes & sales in the MVP (moved from v1.1) | Staff's main job is recording sales; without recipes the staff role is almost empty | ~1 extra week; v1.0 target moves to 13 December |
| Only the owner records deliveries | Owner handles invoices and prices | Delivery may be entered after it arrives → `delivered_on` field |
| Staff don't see ingredient stock or prices | Owner's choice; staff only need dish availability | Two views of the same data |
| Negative stock allowed | Real sales must never be rejected | Reports can show negative numbers |
| Deactivate, never delete users | History keeps who did what | Inactive users stay in the table |
| Shared DB + `restaurant_id` | Simple to run and migrate | Isolation depends on every query → enforced by one helper and tests |
| JWT 8 h, no refresh | Simple; one login per shift | User logs in again after 8 h |
| PDF uploads postponed | Needs storage, limits and backups | Invoices are kept outside the app for now |
