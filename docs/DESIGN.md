# Dispensa — Design Document

> Author: Aref Haghgoorostami · Status: Draft · Last updated: YYYY-MM-DD
> Write each section yourself. Keep it short: clear sentences, diagrams, tables.

## 1. Requirements
- **Users and what they need to do** (owner, staff)
- **Functional requirements:** what the system must do
- **Non-functional requirements:** security, data correctness, availability, performance targets
- **Scale assumptions:** how many restaurants, users, movements per day (realistic numbers)
- **Out of scope**

## 2. Architecture
- Diagram: client → HTTPS → reverse proxy → app → database
- What each component does, and why it's there
- Why a single server is the right choice today

## 3. API design
- Resources and endpoints
- Conventions: naming, status codes, error format, pagination, versioning

## 4. Authentication, authorization & tenancy
- How login works (step by step)
- Roles and what each can do
- How data from different restaurants is kept separate, and why this approach

## 5. Data model
- Entity diagram (tables and relationships)
- Keys, constraints, and what each constraint protects

## 6. Consistency
- The stock ledger: why movements instead of an editable quantity
- Transactions: which operations must be all-or-nothing
- Concurrent writes: what happens when two people act at the same time

## 7. Performance
- The most frequent queries
- Indexes needed, and why
- Caching: why not yet, and when it would be needed

## 8. Operations
- Deployment: how code gets from GitHub to the server
- Backups and restore
- Logging, monitoring, error tracking
- Failure scenarios: server down, database full, bad deploy — what happens, and how to recover

## 9. Scaling path & trade-offs
- What breaks first as usage grows, and the next step for each
- Key decisions, the alternatives considered, and why this choice

## 10. Changes log
- Decisions that changed during implementation, and why
