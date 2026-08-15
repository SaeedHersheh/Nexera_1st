from __future__ import annotations

from app.services.road_graph_service import RoadGraphService


class TurnInstructionEngine:
    def __init__(
        self,
        road_service: RoadGraphService,
    ):
        self.road = road_service

        self.min_turn_angle = 35
        self.max_turn_angle = 150

        self.max_search_distance_m = 2500
        self.max_steps = 60

    def _usable_edges(
        self,
        graph,
        current_node: int,
        previous_node: int | None,
    ) -> list[dict]:

        edges = self.road.get_outgoing_edges(
            graph,
            current_node,
        )

        if previous_node is not None:
            edges = [
                edge
                for edge in edges
                if edge["to_node"] != previous_node
            ]

        return [
            edge
            for edge in edges
            if edge["bearing"] is not None
        ]

    def _classify_edges(
        self,
        edges: list[dict],
        incoming_bearing: float,
    ) -> list[dict]:

        classified = []

        for edge in edges:
            angle = self.road.turn_angle(
                incoming_bearing,
                edge["bearing"],
            )

            classified.append(
                {
                    **edge,
                    "turn_angle": round(angle, 2),
                }
            )

        return classified

    def _right_turns(
        self,
        edges: list[dict],
    ) -> list[dict]:

        return [
            edge
            for edge in edges
            if (
                self.min_turn_angle
                <= edge["turn_angle"]
                <= self.max_turn_angle
            )
        ]

    def _left_turns(
        self,
        edges: list[dict],
    ) -> list[dict]:

        return [
            edge
            for edge in edges
            if (
                -self.max_turn_angle
                <= edge["turn_angle"]
                <= -self.min_turn_angle
            )
        ]

    @staticmethod
    def _straightest_edge(
        edges: list[dict],
    ) -> dict | None:

        if not edges:
            return None

        return min(
            edges,
            key=lambda edge: abs(
                edge["turn_angle"]
            ),
        )

    @staticmethod
    def _best_right_turn(
        edges: list[dict],
    ) -> dict | None:

        if not edges:
            return None

        return min(
            edges,
            key=lambda edge: abs(
                edge["turn_angle"] - 90
            ),
        )

    @staticmethod
    def _best_left_turn(
        edges: list[dict],
    ) -> dict | None:

        if not edges:
            return None

        return min(
            edges,
            key=lambda edge: abs(
                edge["turn_angle"] + 90
            ),
        )

    def find_nth_turn(
        self,
        graph,
        anchor_node_id: int,
        order: int,
        direction: str,
    ) -> list[dict]:

        starting_edges = self.road.get_outgoing_edges(
            graph,
            anchor_node_id,
        )

        candidates = []

        for start_edge in starting_edges:
            if start_edge["bearing"] is None:
                continue

            candidate = self._follow_heading(
                graph=graph,
                anchor_node_id=anchor_node_id,
                starting_edge=start_edge,
                required_order=order,
                turn_direction=direction,
            )

            if candidate:
                candidates.append(candidate)

        candidates.sort(
            key=lambda item: (
                item["distance_before_turn_m"],
                abs(abs(item["turn_angle"]) - 90),
            )
        )

        return candidates

    def find_nth_right_turn(
        self,
        graph,
        anchor_node_id: int,
        order: int,
    ) -> list[dict]:

        return self.find_nth_turn(
            graph=graph,
            anchor_node_id=anchor_node_id,
            order=order,
            direction="right",
        )

    def find_nth_left_turn(
        self,
        graph,
        anchor_node_id: int,
        order: int,
    ) -> list[dict]:

        return self.find_nth_turn(
            graph=graph,
            anchor_node_id=anchor_node_id,
            order=order,
            direction="left",
        )

    def _follow_heading(
        self,
        graph,
        anchor_node_id: int,
        starting_edge: dict,
        required_order: int,
        turn_direction: str,
    ) -> dict | None:

        previous_node = anchor_node_id

        current_node = starting_edge["to_node"]

        incoming_bearing = starting_edge[
            "bearing"
        ]

        travelled = starting_edge[
            "length_m"
        ]

        turn_counter = 0

        path = [
            anchor_node_id,
            current_node,
        ]

        for _ in range(self.max_steps):

            if travelled > self.max_search_distance_m:
                return None

            edges = self._usable_edges(
                graph,
                current_node,
                previous_node,
            )

            if not edges:
                return None

            classified = self._classify_edges(
                edges,
                incoming_bearing,
            )

            if turn_direction == "right":
                matching_turns = self._right_turns(
                    classified
                )

            elif turn_direction == "left":
                matching_turns = self._left_turns(
                    classified
                )

            else:
                raise ValueError(
                    f"Unsupported turn direction: "
                    f"{turn_direction}"
                )

            if matching_turns:
                turn_counter += 1

                if turn_counter == required_order:

                    if turn_direction == "right":
                        selected = (
                            self._best_right_turn(
                                matching_turns
                            )
                        )
                    else:
                        selected = (
                            self._best_left_turn(
                                matching_turns
                            )
                        )

                    if selected is None:
                        return None

                    return {
                        "start_heading": {
                            "from_node": (
                                starting_edge[
                                    "from_node"
                                ]
                            ),
                            "to_node": (
                                starting_edge[
                                    "to_node"
                                ]
                            ),
                            "bearing": (
                                starting_edge[
                                    "bearing"
                                ]
                            ),
                        },

                        "turn_direction": (
                            turn_direction
                        ),

                        "turn_number": (
                            turn_counter
                        ),

                        "intersection_node": (
                            current_node
                        ),

                        "turn_to_node": (
                            selected["to_node"]
                        ),

                        "turn_edge_key": (
                            selected["key"]
                        ),

                        "turn_angle": (
                            selected["turn_angle"]
                        ),

                        "turn_edge_length_m": (
                            selected["length_m"]
                        ),

                        "turn_edge_bearing": (
                            selected["bearing"]
                        ),

                        "distance_before_turn_m": (
                            round(
                                travelled,
                                2,
                            )
                        ),

                        "path_before_turn": (
                            path.copy()
                        ),
                    }

            continuation = (
                self._straightest_edge(
                    classified
                )
            )

            if continuation is None:
                return None

            previous_node = current_node

            current_node = continuation[
                "to_node"
            ]

            incoming_bearing = continuation[
                "bearing"
            ]

            travelled += continuation[
                "length_m"
            ]

            path.append(current_node)

        return None

    def _point_on_edge(
        self,
        graph,
        from_node: int,
        to_node: int,
        key: int,
        distance_m: float,
    ) -> dict:

        edge_data = graph.get_edge_data(
            from_node,
            to_node,
            key,
        )

        if edge_data is None:
            raise ValueError(
                "Road edge not found."
            )

        edge_length = float(
            edge_data.get(
                "length",
                0,
            )
        )

        if edge_length <= 0:
            raise ValueError(
                "Road edge has invalid length."
            )

        fraction = min(
            max(
                distance_m / edge_length,
                0.0,
            ),
            1.0,
        )

        geometry = edge_data.get(
            "geometry"
        )

        if geometry is not None:
            point = geometry.interpolate(
                fraction,
                normalized=True,
            )

            latitude = float(
                point.y
            )

            longitude = float(
                point.x
            )

        else:
            start = graph.nodes[
                from_node
            ]

            end = graph.nodes[
                to_node
            ]

            latitude = (
                float(start["y"])
                + (
                    float(end["y"])
                    - float(start["y"])
                )
                * fraction
            )

            longitude = (
                float(start["x"])
                + (
                    float(end["x"])
                    - float(start["x"])
                )
                * fraction
            )

        return {
            "latitude": latitude,
            "longitude": longitude,

            "distance_on_edge_m": round(
                distance_m,
                2,
            ),

            "edge_length_m": round(
                edge_length,
                2,
            ),

            "fraction": round(
                fraction,
                4,
            ),
        }

    def move_after_turn(
        self,
        graph,
        turn_candidate: dict,
        distance_m: float,
    ) -> dict | None:

        intersection_node = (
            turn_candidate[
                "intersection_node"
            ]
        )

        turn_to_node = (
            turn_candidate[
                "turn_to_node"
            ]
        )

        turn_edge_key = (
            turn_candidate[
                "turn_edge_key"
            ]
        )

        turn_edge_length = float(
            turn_candidate[
                "turn_edge_length_m"
            ]
        )

        # Destination is located inside
        # the road segment we just entered.
        if distance_m <= turn_edge_length:

            point = self._point_on_edge(
                graph=graph,
                from_node=intersection_node,
                to_node=turn_to_node,
                key=turn_edge_key,
                distance_m=distance_m,
            )

            return {
                **point,

                "travelled_m": round(
                    distance_m,
                    2,
                ),

                "inside_turn_edge": True,

                "path": [
                    intersection_node,
                    turn_to_node,
                ],
            }

        remaining = (
            distance_m
            - turn_edge_length
        )

        continuation = self.move_forward(
            graph=graph,
            start_node=turn_to_node,
            previous_node=intersection_node,
            incoming_bearing=turn_candidate[
                "turn_edge_bearing"
            ],
            distance_m=remaining,
        )

        if continuation is None:
            return None

        continuation[
            "travelled_m"
        ] = round(
            distance_m,
            2,
        )

        continuation[
            "inside_turn_edge"
        ] = False

        continuation[
            "path"
        ] = (
            [intersection_node]
            + continuation.get(
                "path",
                [],
            )
        )

        return continuation

    def move_forward(
        self,
        graph,
        start_node: int,
        previous_node: int,
        incoming_bearing: float,
        distance_m: float,
    ) -> dict | None:

        current_node = start_node

        travelled = 0.0

        path = [
            previous_node,
            current_node,
        ]

        for _ in range(
            self.max_steps
        ):

            current_data = (
                graph.nodes[
                    current_node
                ]
            )

            if travelled >= distance_m:
                return {
                    "latitude": float(
                        current_data["y"]
                    ),

                    "longitude": float(
                        current_data["x"]
                    ),

                    "travelled_m": round(
                        travelled,
                        2,
                    ),

                    "path": path,
                }

            edges = self._usable_edges(
                graph,
                current_node,
                previous_node,
            )

            if not edges:
                return {
                    "latitude": float(
                        current_data["y"]
                    ),

                    "longitude": float(
                        current_data["x"]
                    ),

                    "travelled_m": round(
                        travelled,
                        2,
                    ),

                    "path": path,
                }

            classified = (
                self._classify_edges(
                    edges,
                    incoming_bearing,
                )
            )

            continuation = (
                self._straightest_edge(
                    classified
                )
            )

            if continuation is None:
                return None

            edge_length = (
                continuation[
                    "length_m"
                ]
            )

            if (
                travelled
                + edge_length
                >= distance_m
            ):
                remaining = (
                    distance_m
                    - travelled
                )

                fraction = (
                    remaining
                    / edge_length
                    if edge_length > 0
                    else 0
                )

                start_data = (
                    graph.nodes[
                        current_node
                    ]
                )

                end_data = (
                    graph.nodes[
                        continuation[
                            "to_node"
                        ]
                    ]
                )

                latitude = (
                    float(
                        start_data[
                            "y"
                        ]
                    )
                    + (
                        float(
                            end_data[
                                "y"
                            ]
                        )
                        - float(
                            start_data[
                                "y"
                            ]
                        )
                    )
                    * fraction
                )

                longitude = (
                    float(
                        start_data[
                            "x"
                        ]
                    )
                    + (
                        float(
                            end_data[
                                "x"
                            ]
                        )
                        - float(
                            start_data[
                                "x"
                            ]
                        )
                    )
                    * fraction
                )

                return {
                    "latitude": latitude,
                    "longitude": longitude,

                    "travelled_m": round(
                        distance_m,
                        2,
                    ),

                    "path": (
                        path
                        + [
                            continuation[
                                "to_node"
                            ]
                        ]
                    ),
                }

            travelled += edge_length

            previous_node = current_node

            current_node = (
                continuation[
                    "to_node"
                ]
            )

            incoming_bearing = (
                continuation[
                    "bearing"
                ]
            )

            path.append(
                current_node
            )

        return None
