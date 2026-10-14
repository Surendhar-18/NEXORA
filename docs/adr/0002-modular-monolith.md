# ADR 0002: Modular Monolith Architecture for Backend

**Status:** Accepted  
**Date:** 2026-10-09  
**Decision-Makers:** Core Architecture Team  

---

## Context
A key design choice is whether to structure NEXORA as a set of distributed microservices (e.g. separate Video Ingestion Service, Detection Service, Routing Service, and Incident Service) or as a cohesive modular monolith.

## Decision
We architect the backend as a **modular monolith** within a single FastAPI application, enforcing strict module separation through domain packages:
- `app.api.v1` (routes/controllers)
- `app.services` (business logic: vision, routing, incidents, rules)
- `app.models` (SQLAlchemy relational entities)
- `app.schemas` (Pydantic DTOs and contracts)

## Alternatives Considered
1. **Microservices Architecture (Docker Compose / Kubernetes):** Deploying separate services for video ingestion, AI detection, routing, and incident tracking communicating via HTTP or message queues (RabbitMQ/Kafka).
2. **Serverless Functions (AWS Lambda / Cloud Run):** Splitting API routes into independent serverless handlers.

## Rationale
- **Zero Network Latency:** Passing raw video frames and heavy numpy image matrices over network serialization protocols between microservices creates massive latency and serialization overhead.
- **Development Simplicity:** A single repository and process avoids distributed transaction complexity, service mesh overhead, and networking failures during live demonstrations.
- **Clean Boundaries:** Internal modules communicate through explicit Python interfaces, preserving future extraction into standalone microservices if needed.

## Consequences
- **Positive:** Single process to start, shared in-memory access where appropriate, simplified database transactions, straightforward debugging.
- **Negative:** Heavy video processing tasks must be handled with care using background threads/processes to prevent event-loop blocking.

---
