# ADR 0007: Simulated Operational Entities for Resource Assignment

**Status:** Accepted  
**Date:** 2026-10-09  
**Decision-Makers:** Core Architecture Team  

---

## Context
A complete emergency management platform must demonstrate how emergency responders (paramedic squads, crowd wardens, security patrols) are assigned to incidents and how their availability impacts operational capability. The architectural question is whether to simulate these response assets in software or attempt integration with real-world telematics/dispatch systems.

## Decision
We model response units as **simulated database entities** managed within the local application, explicitly labeled in the UI and documentation as demonstration resources.

## Alternatives Considered
1. **Live GPS Telematics / External CAD Integration:** Interfacing with physical CAD (Computer-Aided Dispatch) APIs or live smartphone GPS feeds from actual responders.
2. **Static Mock Objects:** Hardcoding resource names directly in frontend component JSX without database persistence or state management.

## Rationale
- **Feasibility & Scope:** Integrating with real public safety emergency dispatch systems (e.g. 112/911/CAD networks) requires government security clearances, cellular hardware, and proprietary protocols that are impossible and inappropriate for a hackathon prototype.
- **Stateful Lifecycle Demonstration:** Rather than superficial static mocks, simulated database entities possess genuine state machines (`available` ↔ `assigned` ↔ `offline`). When an operator assigns a medical team to an incident, the database updates, the team is removed from the available pool, and the action is recorded in the audit log.
- **Honest Prototype Scope:** Explicitly documenting resources as simulated prevents misleading evaluators into believing live emergency services are wired to the application.

## Consequences
- **Positive:** Enables a realistic, stateful end-to-end incident dispatch experience; fully controllable and testable in local development.
- **Negative:** Telematics tracking (live GPS breadcrumb updates) is out of scope for the MVP.

---
