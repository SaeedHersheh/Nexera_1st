from __future__ import annotations

import math

import networkx as nx

from app.algorithms.fibonacci_heap import (
    FibonacciHeap,
)

from app.services.road_graph_service import (
    RoadGraphService,
)


class GraphPathfinder:
    def __init__(
        self,
        road_service: RoadGraphService,
    ):
        self.road = road_service

    def _heuristic(
        self,
        graph,
        node_a: int,
        node_b: int,
    ) -> float:

        a = graph.nodes[node_a]
        b = graph.nodes[node_b]

        return self.road.haversine_m(
            lat1=float(a["y"]),
            lon1=float(a["x"]),
            lat2=float(b["y"]),
            lon2=float(b["x"]),
        )

    def dijkstra(
        self,
        graph,
        source_node: int,
        target_node: int,
    ) -> dict:

        path = nx.dijkstra_path(
            graph,
            source=source_node,
            target=target_node,
            weight="length",
        )

        distance = nx.dijkstra_path_length(
            graph,
            source=source_node,
            target=target_node,
            weight="length",
        )

        return {
            "algorithm": "dijkstra",
            "distance_m": round(
                float(distance),
                2,
            ),
            "node_count": len(path),
            "path": [
                int(node)
                for node in path
            ],
        }

    def astar(
        self,
        graph,
        source_node: int,
        target_node: int,
    ) -> dict:

        heuristic = lambda u, v: (
            self._heuristic(
                graph,
                u,
                v,
            )
        )

        path = nx.astar_path(
            graph,
            source=source_node,
            target=target_node,
            heuristic=heuristic,
            weight="length",
        )

        distance = nx.astar_path_length(
            graph,
            source=source_node,
            target=target_node,
            heuristic=heuristic,
            weight="length",
        )

        return {
            "algorithm": "astar",
            "distance_m": round(
                float(distance),
                2,
            ),
            "node_count": len(path),
            "path": [
                int(node)
                for node in path
            ],
        }

    def fibonacci_dijkstra(
        self,
        graph,
        source_node: int,
        target_node: int,
    ) -> dict:
        """
        Dijkstra implemented using a Fibonacci Heap.

        Priority queue operations use:
        - insert
        - extract_min
        - decrease_key
        """

        infinity = math.inf

        distances = {
            node: infinity
            for node in graph.nodes
        }

        previous = {}

        heap = FibonacciHeap()

        handles = {}

        # Insert all graph nodes.
        for node in graph.nodes:
            handles[node] = heap.insert(
                infinity,
                node,
            )

        distances[source_node] = 0.0

        heap.decrease_key(
            handles[source_node],
            0.0,
        )

        visited = set()

        while not heap.is_empty():

            minimum = heap.extract_min()

            if minimum is None:
                break

            current_node = minimum.value
            current_distance = minimum.key

            if current_distance == infinity:
                break

            if current_node in visited:
                continue

            visited.add(
                current_node
            )

            if current_node == target_node:
                break

            for (
                _,
                neighbor,
                key,
                edge_data,
            ) in graph.out_edges(
                current_node,
                keys=True,
                data=True,
            ):

                if neighbor in visited:
                    continue

                edge_length = float(
                    edge_data.get(
                        "length",
                        1.0,
                    )
                )

                candidate_distance = (
                    current_distance
                    + edge_length
                )

                if (
                    candidate_distance
                    < distances[neighbor]
                ):
                    distances[
                        neighbor
                    ] = candidate_distance

                    previous[
                        neighbor
                    ] = current_node

                    heap.decrease_key(
                        handles[neighbor],
                        candidate_distance,
                    )

        if (
            distances[target_node]
            == infinity
        ):
            raise nx.NetworkXNoPath(
                f"No path between "
                f"{source_node} and "
                f"{target_node}"
            )

        path = []

        current = target_node

        while True:
            path.append(
                current
            )

            if current == source_node:
                break

            if current not in previous:
                raise nx.NetworkXNoPath(
                    "Path reconstruction failed."
                )

            current = previous[
                current
            ]

        path.reverse()

        return {
            "algorithm": (
                "dijkstra_fibonacci_heap"
            ),

            "distance_m": round(
                float(
                    distances[
                        target_node
                    ]
                ),
                2,
            ),

            "node_count": len(
                path
            ),

            "visited_nodes": len(
                visited
            ),

            "path": [
                int(node)
                for node in path
            ],
        }

    def compare_all(
        self,
        graph,
        source_node: int,
        target_node: int,
    ) -> dict:

        dijkstra_result = self.dijkstra(
            graph,
            source_node,
            target_node,
        )

        astar_result = self.astar(
            graph,
            source_node,
            target_node,
        )

        fibonacci_result = (
            self.fibonacci_dijkstra(
                graph,
                source_node,
                target_node,
            )
        )

        distances = [
            dijkstra_result[
                "distance_m"
            ],
            astar_result[
                "distance_m"
            ],
            fibonacci_result[
                "distance_m"
            ],
        ]

        return {
            "dijkstra": (
                dijkstra_result
            ),

            "astar": (
                astar_result
            ),

            "fibonacci_dijkstra": (
                fibonacci_result
            ),

            "all_same_distance": (
                max(distances)
                - min(distances)
                < 0.5
            ),
        }
