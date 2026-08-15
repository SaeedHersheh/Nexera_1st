from __future__ import annotations

from statistics import mean

from app.nlp.parser import parse_descriptive_address
from app.services.instruction_model import build_instruction_model
from app.services.road_graph_service import RoadGraphService
from app.services.spatial_validator import SpatialValidator
from app.services.turn_instruction_engine import TurnInstructionEngine


class NavigationResolver:
    def __init__(
        self,
        radius_meters: int = 1500,
    ):
        self.road = RoadGraphService(
            radius_meters=radius_meters,
        )

        self.turn_engine = TurnInstructionEngine(
            road_service=self.road,
        )

        self.spatial_validator = SpatialValidator()

    def _get_navigation_instructions(
        self,
        instruction_model: dict,
    ):
        turn_instruction = None
        distance_instruction = None

        for instruction in instruction_model.get(
            "instructions",
            [],
        ):
            if (
                instruction.get("type") == "turn"
                and turn_instruction is None
            ):
                turn_instruction = instruction

            elif (
                instruction.get("type") == "distance"
                and distance_instruction is None
            ):
                distance_instruction = instruction

        return (
            turn_instruction,
            distance_instruction,
        )

    def _get_validation_landmarks(
        self,
        parsed: dict,
        anchor: dict,
    ) -> list[dict]:
        """
        Landmarks other than the anchor are used
        to validate candidate destination points.

        Example:
        دوار ياسين = anchor
        صيدلية الامل = validation landmark
        """

        validation_landmarks = []

        anchor_place_id = anchor.get(
            "place_id"
        )

        anchor_position = anchor.get(
            "position",
            -1,
        )

        for landmark in parsed.get(
            "landmarks",
            [],
        ):
            if (
                landmark.get("place_id")
                == anchor_place_id
            ):
                continue

            # Prefer landmarks appearing after
            # the anchor in the address.
            if (
                landmark.get("position", 0)
                <= anchor_position
            ):
                continue

            validation_landmarks.append(
                landmark
            )

        return validation_landmarks

    def _validate_candidate(
        self,
        candidate: dict,
        validation_landmarks: list[dict],
        area_name: str | None,
    ) -> dict:

        final_point = candidate[
            "final_point"
        ]

        validations = []

        for landmark in validation_landmarks:

            relation = landmark.get(
                "relation"
            )

            validation = (
                self.spatial_validator.validate_landmark(
                    expected_text=landmark[
                        "text"
                    ],
                    latitude=final_point[
                        "latitude"
                    ],
                    longitude=final_point[
                        "longitude"
                    ],
                    relation=relation,
                    area_name=area_name,
                    expected_type=landmark.get(
                        "type"
                    ),
                )
            )

            validations.append(
                {
                    "landmark": landmark[
                        "text"
                    ],
                    "relation": relation,
                    "matched": validation[
                        "matched"
                    ],
                    "best_match": validation[
                        "best_match"
                    ],
                    "relation_max_distance_m": (
                        validation[
                            "relation_max_distance_m"
                        ]
                    ),
                }
            )

        return {
            "validations": validations,
            "validation_count": len(
                validations
            ),
        }

    def _calculate_final_confidence(
        self,
        navigation_confidence: float,
        validations: list[dict],
    ) -> float:
        """
        MVP heuristic confidence.

        Navigation geometry = 60%
        Spatial landmark validation = 40%
        """

        if not validations:
            return round(
                navigation_confidence,
                3,
            )

        validation_scores = []

        for validation in validations:

            best_match = validation.get(
                "best_match"
            )

            if (
                validation.get("matched")
                and best_match
            ):
                validation_scores.append(
                    best_match.get(
                        "validation_score",
                        0.0,
                    )
                )
            else:
                validation_scores.append(
                    0.0
                )

        spatial_confidence = mean(
            validation_scores
        )

        final_confidence = (
            navigation_confidence * 0.60
            + spatial_confidence * 0.40
        )

        return round(
            min(
                max(
                    final_confidence,
                    0.0,
                ),
                1.0,
            ),
            3,
        )

    def resolve(
        self,
        raw_address: str,
    ) -> dict:

        # ---------------------------------
        # 1. NLP
        # ---------------------------------

        parsed = parse_descriptive_address(
            raw_address
        )

        instruction_model = (
            build_instruction_model(
                parsed
            )
        )

        anchor = instruction_model.get(
            "anchor"
        )

        if not anchor:
            return {
                "status": "anchor_not_found",
                "raw_address": raw_address,
                "parsed": parsed,
            }

        latitude = anchor.get(
            "latitude"
        )

        longitude = anchor.get(
            "longitude"
        )

        if (
            latitude is None
            or longitude is None
        ):
            return {
                "status": (
                    "anchor_has_no_coordinates"
                ),
                "raw_address": raw_address,
                "anchor": anchor,
            }

        # ---------------------------------
        # 2. Navigation instructions
        # ---------------------------------

        (
            turn_instruction,
            distance_instruction,
        ) = self._get_navigation_instructions(
            instruction_model
        )

        if turn_instruction is None:
            return {
                "status": (
                    "turn_instruction_not_found"
                ),
                "raw_address": raw_address,
                "anchor": anchor,
            }

        turn_order = turn_instruction.get(
            "order"
        )

        turn_direction = (
            turn_instruction.get(
                "direction"
            )
        )

        if (
            turn_order is None
            or turn_direction
            not in {
                "right",
                "left",
            }
        ):
            return {
                "status": (
                    "invalid_turn_instruction"
                ),
                "raw_address": raw_address,
                "turn_instruction": (
                    turn_instruction
                ),
            }

        distance_m = 0.0

        if distance_instruction:
            distance_m = float(
                distance_instruction.get(
                    "meters",
                    0,
                )
            )

        # ---------------------------------
        # 3. Validation landmarks
        # ---------------------------------

        validation_landmarks = (
            self._get_validation_landmarks(
                parsed,
                anchor,
            )
        )

        administrative_areas = (
            parsed.get(
                "administrative_areas",
                {},
            )
        )

        area_name = (
            administrative_areas.get(
                "neighborhood"
            )
            or administrative_areas.get(
                "locality"
            )
            or administrative_areas.get(
                "city"
            )
            or administrative_areas.get(
                "governorate"
            )
        )

        # ---------------------------------
        # 4. Road graph
        # ---------------------------------

        graph = self.road.load_graph(
            latitude=latitude,
            longitude=longitude,
        )

        snapped_anchor = (
            self.road.snap_to_nearest_node(
                graph,
                latitude=latitude,
                longitude=longitude,
            )
        )

        # ---------------------------------
        # 5. Execute turn
        # ---------------------------------

        turn_candidates = (
            self.turn_engine.find_nth_turn(
                graph=graph,
                anchor_node_id=(
                    snapped_anchor[
                        "node_id"
                    ]
                ),
                order=turn_order,
                direction=turn_direction,
            )
        )

        if not turn_candidates:
            return {
                "status": "turn_not_found",
                "raw_address": raw_address,
                "anchor": anchor,
                "snapped_anchor": (
                    snapped_anchor
                ),
            }

        # ---------------------------------
        # 6. Resolve candidate endpoints
        # ---------------------------------

        resolved_candidates = []

        for index, turn_candidate in enumerate(
            turn_candidates,
            start=1,
        ):

            if distance_m > 0:

                final_point = (
                    self.turn_engine.move_after_turn(
                        graph=graph,
                        turn_candidate=turn_candidate,
                        distance_m=distance_m,
                    )
                )

            else:
                node = graph.nodes[
                    turn_candidate[
                        "turn_to_node"
                    ]
                ]

                final_point = {
                    "latitude": float(
                        node["y"]
                    ),
                    "longitude": float(
                        node["x"]
                    ),
                    "travelled_m": 0.0,
                }

            if final_point is None:
                continue

            # -----------------------------
            # Navigation confidence
            # -----------------------------

            angle = abs(
                turn_candidate[
                    "turn_angle"
                ]
            )

            navigation_confidence = max(
                0.0,
                1.0
                - (
                    abs(
                        angle - 90
                    )
                    / 90
                ),
            )

            candidate = {
                "candidate_id": index,

                "turn": {
                    "direction": (
                        turn_direction
                    ),

                    "order": (
                        turn_order
                    ),

                    "angle": (
                        turn_candidate[
                            "turn_angle"
                        ]
                    ),

                    "distance_before_turn_m": (
                        turn_candidate[
                            "distance_before_turn_m"
                        ]
                    ),

                    "intersection_node": (
                        turn_candidate[
                            "intersection_node"
                        ]
                    ),
                },

                "distance_after_turn_m": (
                    distance_m
                ),

                "final_point": (
                    final_point
                ),

                "navigation_confidence": (
                    round(
                        navigation_confidence,
                        3,
                    )
                ),

                "path_before_turn": (
                    turn_candidate[
                        "path_before_turn"
                    ]
                ),
            }

            # -----------------------------
            # Spatial validation
            # -----------------------------

            validation_result = (
                self._validate_candidate(
                    candidate,
                    validation_landmarks,
                    area_name,
                )
            )

            candidate.update(
                validation_result
            )

            candidate[
                "final_confidence"
            ] = (
                self._calculate_final_confidence(
                    navigation_confidence,
                    candidate[
                        "validations"
                    ],
                )
            )

            resolved_candidates.append(
                candidate
            )

        if not resolved_candidates:
            return {
                "status": (
                    "navigation_failed"
                ),
                "raw_address": raw_address,
            }

        # ---------------------------------
        # 7. Rank candidates
        # ---------------------------------

        resolved_candidates.sort(
            key=lambda candidate: (
                -candidate[
                    "final_confidence"
                ],
                candidate[
                    "turn"
                ][
                    "distance_before_turn_m"
                ],
            )
        )

        best_candidate = (
            resolved_candidates[0]
        )

        # Ambiguous only if multiple
        # candidates are close in score.
        ambiguous = False

        if len(resolved_candidates) > 1:
            score_difference = (
                resolved_candidates[0][
                    "final_confidence"
                ]
                - resolved_candidates[1][
                    "final_confidence"
                ]
            )

            ambiguous = (
                score_difference < 0.10
            )

        return {
            "status": "resolved",

            "raw_address": raw_address,

            "administrative_area": (
                area_name
            ),

            "anchor": anchor,

            "anchor_relation": (
                instruction_model.get(
                    "anchor_relation"
                )
            ),

            "snapped_anchor": (
                snapped_anchor
            ),

            "instructions": (
                instruction_model.get(
                    "instructions",
                    [],
                )
            ),

            "validation_landmarks": [
                {
                    "text": landmark[
                        "text"
                    ],
                    "relation": landmark.get(
                        "relation"
                    ),
                    "type": landmark.get(
                        "type"
                    ),
                }
                for landmark
                in validation_landmarks
            ],

            "candidate_count": len(
                resolved_candidates
            ),

            "ambiguous": ambiguous,

            "best_candidate": (
                best_candidate
            ),

            "final_destination": (
                best_candidate[
                    "final_point"
                ]
            ),

            "final_confidence": (
                best_candidate[
                    "final_confidence"
                ]
            ),

            "candidates": (
                resolved_candidates
            ),
        }
