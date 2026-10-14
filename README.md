# NEXORA — AI-Powered Crowd Safety & Emergency Response

## Overview

NEXORA is a decision-support prototype designed to help event operators monitor crowd conditions, review potential safety risks, coordinate response resources, and evaluate alternative routes during large public gatherings.

It integrates **VisionX**, the project's video analytics module, with a GIS-based emergency operations workspace.

## Problem

Large gatherings can create crowd congestion, obstructed walkways, delayed incident reporting, and difficulties coordinating emergency response teams. Operators need a clearer way to review potential risks and organize their response.

## Our Solution

NEXORA combines video-based person detection, configurable crowd-risk rules, human-reviewed events, incident management, simulated response resources, and GIS route alternatives in one operational dashboard.

## Key Features

- **VisionX video analytics:** Upload recorded video, sample frames, and run YOLO-based person detection with bounding-box evidence.
- **Crowd-risk rules:** Evaluate configured thresholds and duration conditions against sampled-frame detection data.
- **Event review:** Let operators inspect, acknowledge, or dismiss potential crowd events before escalation.
- **Incident management:** Track incidents through a validated lifecycle, maintain notes and audit history, and assign simulated response teams.
- **GIS operations:** View venue zones and walkways, block or reopen walkways, and calculate alternative routes.
- **Operational analytics:** Review project metrics and export supported reports.
- **Security and auditability:** Validate uploads, preserve operational history, and provide documented safeguards.

## Technology Stack

- Frontend: React, TypeScript, Vite
- Backend: Python, FastAPI
- Database: SQLite with SQLAlchemy
- Computer vision: OpenCV, PyTorch, Ultralytics YOLO
- GIS and routing: Leaflet, NetworkX
- Testing: Pytest and frontend TypeScript/build checks

## Architecture

Recorded Video → OpenCV Frame Sampling → YOLO Person Detection → Configurable Crowd Rules → Human Event Review → Incident Management → Simulated Resource Coordination → GIS Route Evaluation → Dashboard and Reports

## Project Structure

- `backend/` — API, database models and application services
- `frontend/` — React user interface
- `docs/` — architecture, specifications and implementation documentation
- `data/venue/` — demo venue configuration
- `scripts/` — development and demo utilities
- `tests/` — automated tests

## Setup

Use the exact installation instructions and environment variables documented in the project files. Configure the backend and frontend environments, install their dependencies, initialize the database, and start both services using the documented commands.

Backend API documentation, when the local server is running, is available at `/docs`.

## Testing

Run the backend test suite with:

`pytest tests/ -v`

Run the frontend typecheck and production build using the scripts defined in `frontend/package.json`.

Report the results from your actual current environment rather than assuming previous test results guarantee the latest checkout works.

## Important Limitations

- Person detections are not guaranteed to identify every person in a crowded or partially occluded frame.
- Counts are sampled-frame detections, not calibrated crowd-density measurements or unique individual counts.
- Configured crowd-risk rules require human review and are not proof that an emergency is occurring.
- Venue topology and walkway conditions must be verified and kept current.
- Response teams are simulated; the prototype does not dispatch real emergency services.
- Calculated routes are advisory alternatives for operator review, not certified evacuation instructions.
- The prototype does not perform facial recognition or biometric identification.

## Intended Impact

NEXORA aims to improve situational awareness, event review, incident coordination, and route evaluation for large public gatherings.

## License

<<<<<<< HEAD
See the `LICENSE` file for the terms governing use and distribution.
=======
See the `LICENSE` file for the terms governing use and distribution.
>>>>>>> origin/main
>>>>>>><img width="770" height="1884" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/ac945999-11b0-495c-8bb9-633366a2f28c" />

