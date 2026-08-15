import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv


load_dotenv(".env")

BASE_URL = "https://www.aweenrayeh.com/api/v1"


MOCK_CHECKPOINTS = {
    "jenin": [
        {
            "id": "cp_jenin_001",
            "checkpoint": "حاجز الجلمة",
            "city": "جنين",
            "entering_status": "سالك",
            "leaving_status": "أزمة",
        },
        {
            "id": "cp_jenin_002",
            "checkpoint": "حاجز دوتان",
            "city": "جنين",
            "entering_status": "أزمة",
            "leaving_status": "سالك",
        },
        {
            "id": "cp_jenin_003",
            "checkpoint": "حاجز برطعة",
            "city": "جنين",
            "entering_status": "مغلق",
            "leaving_status": "مغلق",
        },
    ]
}


class AweenRayehClient:
    def __init__(self):
        self.api_key = os.getenv("AWEEN_RAYEH_API_KEY")
        self.mock_mode = (
            os.getenv("AWEEN_RAYEH_MOCK", "true").lower() == "true"
        )

    def _headers(self):
        if not self.api_key:
            raise RuntimeError(
                "AWEEN_RAYEH_API_KEY is not configured."
            )

        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }

    def get_status(self):
        if self.mock_mode:
            return {
                "status": "ok",
                "api_version": "v1",
                "mode": "simulation",
            }

        response = requests.get(
            f"{BASE_URL}/status",
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    def get_checkpoints(self):
        if self.mock_mode:
            checkpoints = []

            for city_data in MOCK_CHECKPOINTS.values():
                checkpoints.extend(city_data)

            return self._build_mock_response(
                checkpoints=checkpoints,
                city=None,
            )

        response = requests.get(
            f"{BASE_URL}/checkpoints",
            headers=self._headers(),
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    def get_city_checkpoints(self, city: str):
        city_key = city.strip().lower()

        if self.mock_mode:
            checkpoints = MOCK_CHECKPOINTS.get(city_key, [])

            return self._build_mock_response(
                checkpoints=checkpoints,
                city=city_key,
            )

        response = requests.get(
            f"{BASE_URL}/checkpoints/city/{city_key}",
            headers=self._headers(),
            timeout=10,
        )

        response.raise_for_status()
        return response.json()

    def _build_mock_response(self, checkpoints, city):
        now = datetime.now(timezone.utc).isoformat()

        data = []

        for checkpoint in checkpoints:
            item = checkpoint.copy()
            item["last_updated"] = now
            data.append(item)

        return {
            "data": data,
            "meta": {
                "total": len(data),
                "city": "جنين" if city == "jenin" else city,
                "city_latin": city,
                "polled_at": now,
                "quota_remaining": 487,
                "api_version": "v1",
                "simulation": True,
            },
        }
