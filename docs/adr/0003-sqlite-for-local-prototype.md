# ADR 0003: SQLite for Local Prototype Persistence

**Status:** Accepted  
**Date:** 2026-10-09  
**Decision-Makers:** Core Architecture Team  

---

## Context
NEXORA requires persistent storage for video metadata, processing job states, frame counts, crowd alerts, venue configurations, incidents, and audit trails. The database must operate reliably in a local development and hackathon demonstration setting without imposing external server installation hurdles.

## Decision
We select **SQLite with Write-Ahead Logging (WAL)** enabled as the primary database engine for the prototype, accessed via **SQLAlchemy 2.0 ORM**.

## Alternatives Considered
1. **PostgreSQL / TimescaleDB:** Enterprise-grade relational and time-series database. However, it requires running a separate background daemon or Docker container, which introduces friction, credentials setup, and potential startup failure on judges' machines.
2. **MongoDB / NoSQL:** Flexible document storage, but lacks relational integrity checks, ACID foreign-key cascading, and relational join efficiency needed for audit trails and incident linking.
3. **In-Memory Dict / JSON Files:** Simple, but state is lost across server restarts and provides no transactional concurrency or query indexing.

## Rationale
- **Zero Configuration:** SQLite is embedded in Python's standard library; no external service, port binding, or user authentication configuration is required.
- **Portability:** The entire application state resides in a single file (`data/nexora.db`), allowing effortless snapshots, resets, and transfers.
- **Full Relational Power:** Standard SQL foreign keys, unique constraints, and indexes ensure data integrity.
- **WAL Mode Performance:** Write-Ahead Logging allows simultaneous read queries during background worker writes.

## Consequences
- **Positive:** Frictionless setup, instant demo resets via file copy, zero external daemon dependencies.
- **Negative:** Limited high-concurrency write throughput compared to PostgreSQL; acceptable for prototype single-operator workflows. Future migration to PostgreSQL is trivial via SQLAlchemy dialect abstraction.

---
