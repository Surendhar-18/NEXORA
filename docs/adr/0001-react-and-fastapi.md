# ADR 0001: Selection of React and FastAPI Stack

**Status:** Accepted  
**Date:** 2026-10-09  
**Decision-Makers:** Core Architecture Team  

---

## Context
NEXORA requires a high-performance web architecture that bridges computer vision, graph analysis, and interactive GIS mapping. The stack must support rapid hackathon development while providing production-grade typing, async I/O, and rich client-side state manipulation.

## Decision
We select **FastAPI (Python 3.10+)** for the backend API and **React 18 (with Vite)** for the frontend single-page application.

## Alternatives Considered
1. **Django + React:** Django provides built-in ORM and admin interfaces, but its synchronous architecture introduces overhead when dealing with async video job processing and streaming endpoints compared to FastAPI's native `asyncio` and Pydantic validation.
2. **Node.js (Express/NestJS) + React:** While Node.js offers unified JavaScript across frontend and backend, integrating Python-based AI libraries (OpenCV, PyTorch, Ultralytics YOLO) would require complex inter-process communication (IPC) or child processes.
3. **Next.js Full-Stack:** Server-side rendering (SSR) is unnecessary for an authenticated command-centre tool, and running native C++ Python CV bindings within Next.js Node workers is brittle.

## Rationale
- **FastAPI:** Directly hosts PyTorch/Ultralytics and OpenCV in Python without IPC overhead; provides automatic OpenAPI documentation and strict Pydantic v2 data validation.
- **React + Vite:** Industry-standard UI ecosystem with superior integration with Leaflet mapping libraries (`react-leaflet`), high rendering performance, and fast HMR during development.

## Consequences
- **Positive:** Unified Python runtime for AI, routing (NetworkX), and web API; strict type safety via Pydantic; instant swagger docs at `/docs`.
- **Negative:** Requires running two separate development servers (`uvicorn` on port 8000 and `vite` on port 5173).

---
