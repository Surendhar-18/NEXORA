# NEXORA — GIS and Routing Design

**Document ID:** DOC-010  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. Venue Data Model

The venue is represented as a structured configuration consisting of:

1. **Venue metadata:** Name, centre coordinates, default zoom level.
2. **Zones:** Named polygonal areas representing functional sections of the venue.
3. **Cameras:** Point locations associated with zones.
4. **Nodes:** Points in the routing graph (junctions, exits, gates, points of interest).
5. **Edges:** Walkways connecting nodes, with distance and penalty attributes.

### Data Source
Venue data is stored as a JSON configuration file in `data/venue/demo_venue.json`. This file is loaded at application startup and seeded into the database tables `venue_nodes` and `venue_edges`.

### Separation from OpenStreetMap
- OpenStreetMap provides **background map tiles** (visual context only).
- The **venue routing graph** is explicitly configured and does not rely on OSM data.
- OSM tiles may not contain indoor or temporary venue structures.
- Route calculations use only the configured venue graph.

## 2. Coordinate System and Map Assumptions

| Property | Value |
|----------|-------|
| Coordinate system | WGS 84 (EPSG:4326) — latitude/longitude |
| Map projection | Web Mercator (EPSG:3857) via Leaflet |
| Distance calculation | Euclidean approximation sufficient for small venue areas |
| Tile provider | OpenStreetMap (default: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`) |
| Default zoom | 16–18 (venue-level detail) |
| Map interaction | Pan, zoom, click on elements |

### Demo Venue Location
For the demonstration, the venue is configured at coordinates near **Prayagraj, India** (approximate Kumbh Mela region):
- Centre: `25.4358°N, 81.8463°E`
- This is a fictional venue layout overlaid on a real geographic location for demonstration purposes.

## 3. Zone and Camera Mapping

### Zone Definition

Each zone is defined by:
- **ID:** Unique zone identifier (e.g., `zone_main_gate`)
- **Name:** Human-readable name (e.g., "Main Gate Area")
- **Polygon:** Array of [latitude, longitude] coordinate pairs defining the boundary
- **Colour:** Hex colour for map display
- **Cameras:** List of camera IDs associated with this zone

### Camera Definition

Each camera is defined by:
- **ID:** Unique camera identifier (e.g., `cam_01`)
- **Name:** Human-readable name
- **Position:** Latitude, longitude
- **Zone ID:** The zone this camera monitors
- **Direction:** Optional field of view direction (for display only)

### Zone-Camera Association
- Each camera belongs to exactly one zone.
- A zone can have multiple cameras.
- Video uploads are associated with zones (and by extension, cameras).
- Events inherit their zone from the video job that generated them.

## 4. Node-Edge Graph Design

### Graph Properties

| Property | Value |
|----------|-------|
| Graph type | Weighted, optionally directed |
| Library | NetworkX |
| Node storage | `venue_nodes` table |
| Edge storage | `venue_edges` table |
| Weight attribute | `cost` (computed from formula) |
| Algorithm | Dijkstra's shortest path (default) |
| Alternative routes | Yen's K-shortest paths |

### Node Types

| Type | Purpose | Map Display |
|------|---------|-------------|
| `junction` | Walkway intersection | Small grey circle |
| `exit` | Venue exit point | Green exit icon |
| `gate` | Controlled entry/exit point | Blue gate icon |
| `poi` | Point of interest | Custom icon |

### Graph Construction

```python
# Pseudocode for graph construction
import networkx as nx

G = nx.Graph()  # Undirected by default

# Add nodes
for node in venue_nodes:
    G.add_node(node.id, **node.attributes)

# Add edges (respecting blocked status)
for edge in venue_edges:
    if not edge.is_blocked:
        cost = calculate_cost(edge)
        G.add_edge(edge.from_node_id, edge.to_node_id,
                   id=edge.id, weight=cost,
                   distance=edge.distance_meters,
                   congestion=edge.congestion_penalty,
                   hazard=edge.hazard_penalty)
        # If bidirectional, NetworkX undirected graph handles this automatically
```

## 5. Walkway Attributes

Each walkway (edge) has the following configurable attributes:

| Attribute | Type | Unit | Description |
|-----------|------|------|-------------|
| `distance_meters` | float | metres | Physical length of the walkway |
| `width_meters` | float | metres | Width (informational, not used in cost formula for MVP) |
| `congestion_penalty` | float | cost units | Additional cost for configured congestion |
| `hazard_penalty` | float | cost units | Additional cost for configured hazards |
| `is_bidirectional` | bool | — | Whether traversable in both directions |
| `is_blocked` | bool | — | Whether currently blocked (excluded from routing) |

### Important Clarifications on Penalties
- **Congestion penalty** values are **configured** by the venue setup, not measured in real-time.
- **Hazard penalty** values are **configured** by the operator, not detected automatically.
- The system does **not** claim to measure actual crowd density on walkways or detect hazards automatically.
- These values enable "what-if" scenario modelling (e.g., "what if this walkway is congested?").

## 6. Route Cost Formula

### Formula

```
C(route) = Σ [ distance_meters(e) + congestion_penalty(e) + hazard_penalty(e) ]
            for each edge e in route
```

### Component Details

| Component | Unit | Default Weight | Description |
|-----------|------|---------------|-------------|
| `distance_meters` | metres | 1.0 (direct) | Physical walkway length |
| `congestion_penalty` | cost units | Added directly | Configured congestion cost addition |
| `hazard_penalty` | cost units | Added directly | Configured hazard cost addition |

### Units and Normalisation
- **Total cost** is expressed in **cost units** (a dimensionless composite).
- The dominant component is typically `distance_meters`, making the cost roughly proportional to walking distance.
- Penalties are additive and expressed in the same unit scale as metres.
- Example: A 100m walkway with congestion_penalty=20 and hazard_penalty=10 has total cost = 130.

### Missing Data Handling
- If `congestion_penalty` is NULL or missing: treated as 0.
- If `hazard_penalty` is NULL or missing: treated as 0.
- If `distance_meters` is NULL or missing: **edge is invalid** and excluded from routing.

### Configurable Weights (Future Enhancement)
For MVP, penalties are added directly. A future version could introduce configurable weights:
```
C(route) = Σ [ w_d × distance(e) + w_c × congestion(e) + w_h × hazard(e) ]
```
This is documented but deferred — direct addition is sufficient for the prototype.

## 7. Blocked-Edge Handling

### Block Operation
1. Operator selects a walkway and clicks "Block".
2. API call: `PUT /api/v1/venue/edges/{edge_id}/block`
3. Database: `is_blocked` set to `true`, `blocked_at` and `blocked_by` recorded.
4. NetworkX graph: Edge removed from the graph.
5. Audit log: Entry created.
6. Map display: Walkway rendered as red dashed line.

### Reopen Operation
1. Operator selects a blocked walkway and clicks "Reopen".
2. API call: `PUT /api/v1/venue/edges/{edge_id}/reopen`
3. Database: `is_blocked` set to `false`, `blocked_at` and `blocked_by` cleared.
4. NetworkX graph: Edge re-added with its cost.
5. Audit log: Entry created.
6. Map display: Walkway rendered as normal grey line.

### Graph Consistency
- The NetworkX graph is rebuilt from the database state on each route calculation request (or maintained in-memory with explicit add/remove operations).
- For the prototype, rebuilding from DB on each request is acceptable given the small graph size.

### Validation
- Cannot block an already-blocked walkway (409 Conflict).
- Cannot reopen a walkway that is not blocked (409 Conflict).
- Blocking the last possible path between two nodes is allowed — the system will report "no valid route" rather than preventing the block.

## 8. Route Alternatives

### Algorithm
Use **Yen's K-shortest simple paths** algorithm (available in NetworkX as `nx.shortest_simple_paths`):

```python
import networkx as nx

def find_routes(graph, source, target, max_routes=3):
    try:
        paths = list(
            itertools.islice(
                nx.shortest_simple_paths(graph, source, target, weight='weight'),
                max_routes
            )
        )
        return [build_route_result(path, graph) for path in paths]
    except nx.NetworkXNoPath:
        return []
    except nx.NodeNotFound as e:
        raise ValueError(f"Node not found: {e}")
```

### Route Result Construction
For each route alternative:
1. Sum total cost across all edges.
2. Break down cost into distance, congestion, and hazard components.
3. List segments with their individual costs.
4. Rank routes by total cost (lowest first).
5. Mark the best route.

### Maximum Alternatives
- Default: 3 routes.
- If fewer than 3 distinct routes exist, return all available.
- If only 1 route exists, return it as the sole option.

## 9. No-Valid-Route Behaviour

When no path exists between the selected nodes:

### Detection
```python
except nx.NetworkXNoPath:
    return RouteComparisonResult(
        from_node=source,
        to_node=target,
        routes_found=0,
        routes=[],
        blocked_edges=get_blocked_edge_ids(),
        message="No valid route exists between the selected points. "
                "Some walkways may be blocked."
    )
```

### User Experience
1. Map shows no route overlay.
2. Route panel displays warning message.
3. Lists currently blocked walkways that may be contributing.
4. Suggests: "Review blocked walkways to restore connectivity."

### Causes
- Walkway blockages have disconnected the graph.
- Source and target are in different connected components.
- The venue configuration does not include a path between the nodes.

## 10. Route Visualisation

### Map Rendering

| Element | Style | Description |
|---------|-------|-------------|
| Best route | 4px solid green line | Primary recommended route |
| Alternative routes | 3px solid orange line | Other viable routes |
| Blocked walkways | 3px dashed red line | Currently blocked |
| Open walkways | 2px solid grey line | Normal walkways |
| Route nodes | Highlighted circles | Nodes along the route |
| Start node | Green circle with label | Source point |
| End node | Red circle with label | Destination point |

### Route Information Panel
For each route displayed:
- Route rank (1 = best)
- Total cost
- Total distance (metres)
- Congestion penalty total
- Hazard penalty total
- Number of segments
- Segment-by-segment breakdown (expandable)

### Interactive Behaviour
- Hover over route on map → highlight corresponding panel entry.
- Click route in panel → zoom/pan map to show full route.
- Routes are updated when walkway status changes.

## 11. Demo Venue Data

### Demo Venue: "Triveni Festival Grounds"

A fictional festival venue inspired by large Indian gathering venues, with the following elements:

**Zones (6):**
| ID | Name | Purpose |
|----|------|---------|
| `zone_main_gate` | Main Gate Area | Primary entry/exit point |
| `zone_north_plaza` | North Plaza | Open gathering area |
| `zone_east_wing` | East Wing | Secondary gathering area |
| `zone_south_market` | South Market | Vendor and services area |
| `zone_west_garden` | West Garden | Open space / overflow |
| `zone_central_stage` | Central Stage | Main event area |

**Nodes (12):**
| ID | Type | Zone |
|----|------|------|
| `gate_main` | gate | zone_main_gate |
| `junction_1` | junction | zone_main_gate |
| `junction_2` | junction | zone_north_plaza |
| `junction_3` | junction | zone_east_wing |
| `junction_4` | junction | zone_central_stage |
| `junction_5` | junction | zone_south_market |
| `junction_6` | junction | zone_west_garden |
| `junction_7` | junction | zone_north_plaza |
| `exit_north` | exit | zone_north_plaza |
| `exit_east` | exit | zone_east_wing |
| `exit_south` | exit | zone_south_market |
| `exit_west` | exit | zone_west_garden |

**Edges (15):**
A connected graph ensuring multiple paths between most node pairs.

**Cameras (8):**
Distributed across all zones, each associated with its zone.

### Validation Scenarios

| Scenario | Expected Result |
|----------|----------------|
| Route: gate_main → exit_north | At least 2 route alternatives |
| Route: gate_main → exit_east | At least 1 route |
| Block walk_1_2, route: gate_main → exit_north | Route recalculated via alternative path |
| Block enough edges to disconnect exit_south | "No valid route" message |
| Reopen all edges, route: any pair | All routes available |

## 12. Venue Configuration File Format

```json
{
    "venue_name": "Triveni Festival Grounds",
    "center": {
        "latitude": 25.4358,
        "longitude": 81.8463
    },
    "default_zoom": 17,
    "zones": [
        {
            "id": "zone_main_gate",
            "name": "Main Gate Area",
            "polygon": [
                [25.4355, 81.8455],
                [25.4365, 81.8455],
                [25.4365, 81.8465],
                [25.4355, 81.8465]
            ],
            "color": "#3B82F6",
            "camera_ids": ["cam_01", "cam_02"]
        }
    ],
    "nodes": [
        {
            "id": "gate_main",
            "name": "Main Gate",
            "type": "gate",
            "latitude": 25.4358,
            "longitude": 81.8458,
            "zone_id": "zone_main_gate",
            "capacity": 500
        }
    ],
    "edges": [
        {
            "id": "walk_main_j1",
            "from_node": "gate_main",
            "to_node": "junction_1",
            "name": "Main Gate Approach",
            "distance_meters": 80.0,
            "width_meters": 8.0,
            "congestion_penalty": 10.0,
            "hazard_penalty": 0.0,
            "is_bidirectional": true
        }
    ],
    "cameras": [
        {
            "id": "cam_01",
            "name": "Main Gate Camera 1",
            "latitude": 25.4357,
            "longitude": 81.8459,
            "zone_id": "zone_main_gate",
            "direction": "north"
        }
    ]
}
```

### Configuration Validation
At startup, the venue configuration is validated for:
- All edge `from_node` and `to_node` references exist in nodes.
- All camera `zone_id` references exist in zones.
- All node `zone_id` references exist in zones (if provided).
- Zone polygons have at least 3 points.
- All distances are positive.
- No duplicate IDs.
- Graph connectivity check (warning if disconnected without blocked edges).

---

*End of Document 10 — GIS and Routing Design*
