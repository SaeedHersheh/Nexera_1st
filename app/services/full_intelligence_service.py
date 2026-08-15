from __future__ import annotations

import networkx as nx

from app.nlp.parser import parse_descriptive_address

from app.services.navigation_resolver import (
    NavigationResolver,
)

from app.services.road_graph_service import (
    RoadGraphService,
)

from app.services.graph_pathfinder import (
    GraphPathfinder,
)

from app.services.delivery_route_service import (
    build_delivery_routes,
)


class FullIntelligenceService:
    def __init__(
        self,
        radius_meters: int = 1500,
    ):
        self.navigation = NavigationResolver(
            radius_meters=radius_meters,
        )

        self.road = RoadGraphService(
            radius_meters=radius_meters,
        )

        self.pathfinder = GraphPathfinder(
            road_service=self.road,
        )

    def resolve(
        self,
        raw_address: str,
    ) -> dict:

        # =====================================
        # 1. NLP
        # =====================================

        parsed = parse_descriptive_address(
            raw_address
        )

        # =====================================
        # 2. Navigation Intelligence
        # =====================================

        navigation = self.navigation.resolve(
            raw_address
        )

        if navigation.get("status") != "resolved":
            return {
                "status": "partial",
                "raw_address": raw_address,
                "stage_failed": "navigation",
                "navigation": navigation,
            }

        anchor = navigation["anchor"]

        final_destination = navigation[
            "final_destination"
        ]

        best_candidate = navigation[
            "best_candidate"
        ]

        # =====================================
        # 3. Interpreted navigation distance
        # =====================================

        distance_before_turn = float(
            best_candidate[
                "turn"
            ][
                "distance_before_turn_m"
            ]
        )

        distance_after_turn = float(
            best_candidate[
                "distance_after_turn_m"
            ]
        )

        interpreted_distance_m = (
            distance_before_turn
            + distance_after_turn
        )

        # =====================================
        # 4. Road Graph
        # =====================================

        graph = self.road.load_graph(
            latitude=anchor[
                "latitude"
            ],
            longitude=anchor[
                "longitude"
            ],
        )

        source_node = (
            self.road.snap_to_nearest_node(
                graph,
                latitude=anchor[
                    "latitude"
                ],
                longitude=anchor[
                    "longitude"
                ],
            )
        )

        target_node = (
            self.road.snap_to_nearest_node(
                graph,
                latitude=final_destination[
                    "latitude"
                ],
                longitude=final_destination[
                    "longitude"
                ],
            )
        )

        # =====================================
        # 5. Dijkstra / A* / Fibonacci
        # =====================================

        pathfinding = None

        try:
            comparison = (
                self.pathfinder.compare_all(
                    graph,
                    source_node=source_node[
                        "node_id"
                    ],
                    target_node=target_node[
                        "node_id"
                    ],
                )
            )

            pathfinding = {
                "status": "ok",

                "source_node": (
                    source_node
                ),

                "target_node": (
                    target_node
                ),

                # Important:
                # target is snapped to nearest
                # graph node.
                "target_mode": (
                    "nearest_road_node"
                ),

                **comparison,
            }

        except nx.NetworkXNoPath:
            pathfinding = {
                "status": "no_path",
            }

        except Exception as exc:
            pathfinding = {
                "status": "failed",
                "error": str(exc),
            }

        # =====================================
        # 6. Aween Rayeh + Route Scoring
        # =====================================

        delivery_routing = None

        try:
            delivery_routing = (
                build_delivery_routes(
                    parsed
                )
            )

            # Replace old POI destination
            # with navigation-resolved point.
            delivery_routing[
                "destination"
            ] = {
                "latitude": (
                    final_destination[
                        "latitude"
                    ]
                ),

                "longitude": (
                    final_destination[
                        "longitude"
                    ]
                ),

                "confidence": (
                    navigation.get(
                        "final_confidence"
                    )
                ),

                "source": (
                    "navigation_intelligence"
                ),
            }

        except Exception as exc:
            delivery_routing = {
                "status": "failed",
                "error": str(exc),
            }

        # =====================================
        # 7. Recommended delivery route
        # =====================================

        recommended_route = None
        checkpoint_status = None
        checkpoint_name = None

        if isinstance(
            delivery_routing,
            dict,
        ):
            recommended_route = (
                delivery_routing.get(
                    "recommended_route"
                )
            )

        if recommended_route:

            checkpoints = (
                recommended_route.get(
                    "checkpoints",
                    [],
                )
            )

            if checkpoints:
                checkpoint_name = (
                    checkpoints[0].get(
                        "checkpoint"
                    )
                )

                checkpoint_status = (
                    checkpoints[0].get(
                        "status"
                    )
                )

        # =====================================
        # 8. Final summary
        # =====================================

        summary = {
            "resolved": True,

            "area": navigation.get(
                "administrative_area"
            ),

            "anchor": anchor.get(
                "name"
            ),

            "anchor_relation": (
                navigation.get(
                    "anchor_relation"
                )
            ),

            "final_latitude": (
                final_destination[
                    "latitude"
                ]
            ),

            "final_longitude": (
                final_destination[
                    "longitude"
                ]
            ),

            "final_confidence": (
                navigation.get(
                    "final_confidence"
                )
            ),

            "interpreted_navigation_distance_m": (
                round(
                    interpreted_distance_m,
                    2,
                )
            ),

            "pathfinding_algorithms": [
                "dijkstra",
                "astar",
                "dijkstra_fibonacci_heap",
            ],

            "algorithms_same_distance": (
                pathfinding.get(
                    "all_same_distance"
                )
                if pathfinding
                and pathfinding.get(
                    "status"
                ) == "ok"
                else None
            ),

            "recommended_delivery_route": (
                recommended_route.get(
                    "route_name"
                )
                if recommended_route
                else None
            ),

            "checkpoint": (
                checkpoint_name
            ),

            "checkpoint_status": (
                checkpoint_status
            ),

            "checkpoint_source": (
                delivery_routing.get(
                    "checkpoint_source"
                )
                if isinstance(
                    delivery_routing,
                    dict,
                )
                else None
            ),

            "simulation": (
                delivery_routing.get(
                    "simulation"
                )
                if isinstance(
                    delivery_routing,
                    dict,
                )
                else None
            ),
        }

        # =====================================
        # FINAL RESULT
        # =====================================

        return {
            "status": "resolved",

            "raw_address": raw_address,

            "summary": summary,

            "navigation": navigation,

            "pathfinding": pathfinding,

            "delivery_routing": (
                delivery_routing
            ),
        }
