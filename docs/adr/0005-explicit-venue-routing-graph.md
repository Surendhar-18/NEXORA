# ADR 0005: Explicit Venue Routing Graph with NetworkX

**Status:** Accepted  
**Date:** 2026-10-09  
**Decision-Makers:** Core Architecture Team  

---

## Context
Evacuation route planning and spatial navigation within temporary or structured festival grounds (such as Kumbh Mela, temporary expo arenas, or stadiums) requires pathfinding that accommodates crowd density impedance, barricades, and dynamically closed gates.

## Decision
We construct an **explicit, directed, weighted topological graph** of the venue using **NetworkX**, driven by structured JSON geometry configuration rather than relying on public external routing APIs (e.g. Google Directions, OSRM, Mapbox).

## Alternatives Considered
1. **Public Road Routing APIs (Google Maps / Mapbox / OpenRouteService):** Querying commercial routing engines.
2. **Euclidean / Straight-Line Spatial Distance:** Computing straight-line vectors between coordinates.
3. **Raster Grid Pathfinding (A* on Pixel Bitmap):** Discretizing the venue map into a high-resolution 2D grid.

## Rationale
- **Temporary Internal Topologies:** Commercial routing services map public asphalt streets; they have zero awareness of internal festival corridors, temporary bamboo barricades, security cordons, or pedestrian bridges.
- **Dynamic Choke Point & Blockage Control:** With an explicit NetworkX graph, operators can block a walkway in milliseconds by removing or infinitely weighting an edge (`weight = inf`), immediately forcing Dijkstra's algorithm to compute the safest detour.
- **Crowd Density Weighting:** The cost function directly incorporates crowd counts derived from VisionX camera zones: `Cost = (Distance / Speed) * DensityPenalty`.
- **Zero Network Latency & Offline Independence:** Graph operations run in Python memory in under 5ms without external API rate limits or internet connectivity.

## Consequences
- **Positive:** Instantaneous route recalculation, fine-grained control over venue walkways, deterministic alternative route finding, complete offline capability.
- **Negative:** Requires venue layout geometry (nodes and edges) to be configured in advance via JSON.

---
