import itertools
import logging
from typing import Dict, Any, List, Optional
import networkx as nx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.venue import Venue, VenueNode, VenueEdge

logger = logging.getLogger("nexora.routing_engine")

class RoutingEngine:
    @staticmethod
    def build_venue_graph(db: Session, venue_id: Optional[str] = None) -> tuple[nx.Graph, List[str], Dict[str, VenueNode]]:
        """
        Builds a NetworkX graph from database records.
        Strictly excludes blocked edges.
        Returns: (graph, list_of_blocked_edge_ids, nodes_map)
        """
        if not venue_id:
            venue = db.query(Venue).first()
            if not venue:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No venue found.")
            venue_id = venue.id

        # Query all active nodes
        nodes = db.query(VenueNode).filter(
            VenueNode.venue_id == venue_id,
            VenueNode.is_active == True
        ).all()
        nodes_map = {n.id: n for n in nodes}

        # Query all edges
        edges = db.query(VenueEdge).filter(VenueEdge.venue_id == venue_id).all()
        blocked_edge_ids = [e.id for e in edges if e.is_blocked]

        # Construct NetworkX Graph
        G = nx.Graph()

        for n in nodes:
            G.add_node(
                n.id,
                name=n.name,
                node_type=n.node_type,
                latitude=n.latitude,
                longitude=n.longitude,
                zone_id=n.zone_id,
                capacity=n.capacity
            )

        for e in edges:
            # Exclude blocked edges completely from routing
            if e.is_blocked:
                continue

            # Skip edges whose endpoints are not in active nodes
            if e.from_node_id not in nodes_map or e.to_node_id not in nodes_map:
                continue

            # Calculate cost: distance + congestion + hazard
            dist = float(e.distance_meters if e.distance_meters > 0 else 10.0)
            congestion = float(e.congestion_penalty or 0.0)
            hazard = float(e.hazard_penalty or 0.0)
            cost = max(0.1, dist + congestion + hazard)

            G.add_edge(
                e.from_node_id,
                e.to_node_id,
                id=e.id,
                name=e.name,
                weight=cost,
                distance=dist,
                congestion=congestion,
                hazard=hazard,
                width=e.width_meters,
                is_bidirectional=e.is_bidirectional
            )

        return G, blocked_edge_ids, nodes_map

    @staticmethod
    def calculate_routes(
        db: Session,
        from_node: str,
        to_node: str,
        max_routes: int = 3,
        venue_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates up to max_routes alternative paths using Yen's K-shortest paths algorithm.
        Returns RouteComparisonResponse structure.
        """
        if not from_node or not to_node:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both 'from_node' and 'to_node' must be specified."
            )

        if from_node == to_node:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Origin and destination cannot be the same node."
            )

        G, blocked_edge_ids, nodes_map = RoutingEngine.build_venue_graph(db, venue_id)

        # Validate nodes exist in configured venue
        if from_node not in nodes_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Origin node '{from_node}' does not exist in the configured venue."
            )

        if to_node not in nodes_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destination node '{to_node}' does not exist in the configured venue."
            )

        # If from_node or to_node are not in G (e.g. isolated with no edges at all)
        if from_node not in G or to_node not in G or not nx.has_path(G, from_node, to_node):
            return {
                "from_node": from_node,
                "to_node": to_node,
                "routes_found": 0,
                "routes": [],
                "blocked_edges": blocked_edge_ids,
                "message": (
                    f"No valid route exists between '{from_node}' and '{to_node}'. "
                    f"Some walkways may be blocked or disconnected in the configured graph."
                ),
                "advisory_notice": (
                    "Calculated route alternative for operator review. "
                    "Advisory decision-support only; not certified emergency evacuation advice."
                )
            }

        try:
            # Yen's K-shortest simple paths
            paths = list(
                itertools.islice(
                    nx.shortest_simple_paths(G, from_node, to_node, weight="weight"),
                    max_routes
                )
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return {
                "from_node": from_node,
                "to_node": to_node,
                "routes_found": 0,
                "routes": [],
                "blocked_edges": blocked_edge_ids,
                "message": (
                    f"No valid route exists between '{from_node}' and '{to_node}'. "
                    f"Some walkways may be blocked."
                ),
                "advisory_notice": (
                    "Calculated route alternative for operator review. "
                    "Advisory decision-support only; not certified emergency evacuation advice."
                )
            }

        route_results = []
        for rank_idx, path in enumerate(paths, start=1):
            segments = []
            edge_ids = []
            total_dist = 0.0
            total_congestion = 0.0
            total_hazard = 0.0
            total_cost = 0.0

            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge_data = G[u][v]
                edge_ids.append(edge_data["id"])
                seg_cost = edge_data["weight"]
                seg_dist = edge_data["distance"]
                seg_cong = edge_data["congestion"]
                seg_haz = edge_data["hazard"]

                total_cost += seg_cost
                total_dist += seg_dist
                total_congestion += seg_cong
                total_hazard += seg_haz

                segments.append({
                    "from": u,
                    "to": v,
                    "edge_id": edge_data["id"],
                    "name": edge_data.get("name"),
                    "distance": round(seg_dist, 2),
                    "congestion": round(seg_cong, 2),
                    "hazard": round(seg_haz, 2),
                    "cost": round(seg_cost, 2)
                })

            route_results.append({
                "rank": rank_idx,
                "is_best": (rank_idx == 1),
                "path": path,
                "edge_ids": edge_ids,
                "total_cost": round(total_cost, 2),
                "distance_meters": round(total_dist, 2),
                "congestion_penalty": round(total_congestion, 2),
                "hazard_penalty": round(total_hazard, 2),
                "segments": segments
            })

        return {
            "from_node": from_node,
            "to_node": to_node,
            "routes_found": len(route_results),
            "routes": route_results,
            "blocked_edges": blocked_edge_ids,
            "message": f"Successfully calculated {len(route_results)} route alternative(s).",
            "advisory_notice": (
                "Calculated route alternative for operator review. "
                "Advisory decision-support only; not certified emergency evacuation advice."
            )
        }
