# ADR 0004: Prerecorded Video Analysis Initial Scope

**Status:** Accepted  
**Date:** 2026-10-09  
**Decision-Makers:** Core Architecture Team  

---

## Context
A major operational choice is whether NEXORA should attempt live RTSP/WebRTC multi-camera streaming ingestion or focus on operator-initiated uploads of recorded video clips for the initial MVP prototype.

## Decision
We limit the initial MVP scope to **operator-uploaded, prerecorded video files** (MP4, AVI, MOV), processed in sampled frame batches.

## Alternatives Considered
1. **Live RTSP CCTV Ingestion:** Connecting directly to network camera streams via RTSP/RTMP and running continuous live inference.
2. **Synthetic Data Only:** Simulating crowd numbers with random generators without processing real video footage.

## Rationale
- **Deterministic Evaluation & Demo Reliability:** Live RTSP streaming introduces uncontrollable variables in hackathon settings (network jitter, dropped frames, camera authentication timeouts, bandwidth collapse). Prerecorded clips guarantee reproducible, testable evaluation.
- **Hardware Feasibility:** Continuous real-time inference across 4–8 concurrent video streams requires dedicated multi-GPU hardware. Batch frame sampling (e.g. 1 frame every 2 seconds) on uploaded footage executes smoothly on consumer CPUs.
- **Architectural Modularity:** The frame extraction pipeline (`FrameExtractor`) and detection engine (`VisionXEngine`) operate on individual decoded image frames; connecting an RTSP video capture stream in a future release requires modifying only the frame ingestion source, preserving the entire downstream pipeline.

## Consequences
- **Positive:** Rock-solid presentation reliability; reproducible automated tests; honest disclosure of capabilities without claiming non-existent live CCTV feeds.
- **Negative:** Real-time push notifications from live camera feeds remain a post-MVP roadmap item.

---
