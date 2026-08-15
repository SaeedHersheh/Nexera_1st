from __future__ import annotations

import math

import osmnx as ox


class RoadGraphService:
    def __init__(
        self,
        radius_meters: int = 1500,
        network_type: str = "drive",
    ):
        self.radius_meters = radius_meters
        self.network_type = network_type

    def load_graph(
        self,
        latitude: float,
        longitude: float,
    ):
        """
        Load the drivable road network around a point.
        """

        graph = ox.graph_from_point(
            center_point=(latitude, longitude),
            dist=self.radius_meters,
            network_type=self.network_type,
            simplify=True,
        )

        # Add compass bearing to each road segment.
        graph = ox.bearing.add_edge_bearings(graph)

        return graph

    def snap_to_nearest_node(
        self,
        graph,
        latitude: float,
        longitude: float,
    ) -> dict:
        """
        Snap latitude/longitude to the nearest road node.
        """

        node_id, distance = ox.distance.nearest_nodes(
            graph,
            X=longitude,
            Y=latitude,
            return_dist=True,
        )

        node = graph.nodes[node_id]

        return {
            "node_id": int(node_id),
            "latitude": float(node["y"]),
            "longitude": float(node["x"]),
            "distance_to_road_m": round(
                float(distance),
                2,
            ),
        }

    def get_outgoing_edges(
        self,
        graph,
        node_id: int,
    ) -> list[dict]:
        """
        Return all outgoing drivable edges from a node.
        """

        edges = []

        for u, v, key, data in graph.out_edges(
            node_id,
            keys=True,
            data=True,
        ):
            target_node = graph.nodes[v]

            bearing = data.get("bearing")

            edges.append(
                {
                    "from_node": int(u),
                    "to_node": int(v),
                    "key": int(key),
                    "length_m": float(
                        data.get("length", 0)
                    ),
                    "bearing": (
                        float(bearing)
                        if bearing is not None
                        else None
                    ),
                    "name": data.get("name"),
                    "highway": data.get("highway"),
                    "geometry": data.get("geometry"),
                    "target_latitude": float(
                        target_node["y"]
                    ),
                    "target_longitude": float(
                        target_node["x"]
                    ),
                }
            )

        return edges

    @staticmethod
    def turn_angle(
        incoming_bearing: float,
        outgoing_bearing: float,
    ) -> float:
        """
        Calculate signed turn angle.

        Positive = right
        Negative = left
        Near zero = straight
        """

        return (
            (
                outgoing_bearing
                - incoming_bearing
                + 540
            )
            % 360
        ) - 180

    @staticmethod
    def haversine_m(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate distance between two coordinates in meters.
        """

        earth_radius = 6_371_000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        delta_phi = math.radians(
            lat2 - lat1
        )

        delta_lambda = math.radians(
            lon2 - lon1
        )

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(delta_lambda / 2) ** 2
        )

        return (
            2
            * earth_radius
            * math.atan2(
                math.sqrt(a),
                math.sqrt(1 - a),
            )
        )
