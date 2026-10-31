from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

import app.services.fieldready_service as fieldready_service
from app.config import get_settings
from app.main import app
from app.models.fieldready import FieldReadyRequest

client = TestClient(app)


def test_assessment_distinguishes_active_heat_and_drought_alerts():
    risk = fieldready_service._assess_conditions(
        {
            "alert_status": "available",
            "forecast_status": "available",
            "alerts": [{"event": "Drought Warning"}],
            "forecast_periods": [{"temperature": 97, "temperature_unit": "F"}],
        }
    )

    assert risk["level"] == "elevated"
    assert risk["drought_alert_status"] == "active_alert"
    assert risk["forecast_high_f"] == 97


def test_unavailable_alert_data_is_not_reported_as_no_alert():
    risk = fieldready_service._assess_conditions(
        {
            "alert_status": "unavailable",
            "forecast_status": "available",
            "alerts": [],
            "forecast_periods": [{"temperature": 85, "temperature_unit": "F"}],
        }
    )

    assert risk["level"] == "no_heat_signal"
    assert risk["drought_alert_status"] == "unavailable"
    assert "NWS alert data is unavailable" in risk["summary"]


def test_assessment_marks_both_sources_unavailable():
    risk = fieldready_service._assess_conditions(
        {
            "alert_status": "unavailable",
            "forecast_status": "unavailable",
            "alerts": [],
            "forecast_periods": [],
        }
    )

    assert risk["level"] == "unavailable"
    assert risk["drought_alert_status"] == "unavailable"


def test_untrusted_alert_link_is_replaced_with_official_nws_url():
    fallback = "https://api.weather.gov/alerts/active"

    assert fieldready_service._nws_url_or_fallback("javascript:alert(1)", fallback) == fallback
    assert fieldready_service._nws_url_or_fallback(
        "https://api.weather.gov/alerts/123", fallback
    ) == "https://api.weather.gov/alerts/123"


def test_fetches_alerts_and_forecast_from_nws(monkeypatch):
    class FakeResponse:
        def __init__(self, payload: dict[str, Any]):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def get(self, url: str):
            if "/alerts/active?" in url:
                return FakeResponse(
                    {
                        "features": [
                            {
                                "id": "https://api.weather.gov/alerts/one",
                                "properties": {"event": "Heat Advisory", "headline": "Heat advisory."},
                            }
                        ]
                    }
                )
            if "/points/" in url:
                return FakeResponse(
                    {"properties": {"forecast": "https://api.weather.gov/gridpoints/OAX/1,2/forecast"}}
                )
            return FakeResponse(
                {
                    "properties": {
                        "periods": [
                            {"name": "Today", "temperature": 96, "temperatureUnit": "F", "shortForecast": "Sunny"}
                        ]
                    }
                }
            )

    monkeypatch.setattr(fieldready_service, "_nws_client", lambda _contact: FakeClient())
    conditions = fieldready_service._fetch_official_conditions(41.25, -96, None)

    assert conditions["alert_status"] == "available"
    assert conditions["forecast_status"] == "available"
    assert conditions["alerts"][0]["event"] == "Heat Advisory"
    assert len(conditions["sources"]) == 2
    assert conditions["forecast_periods"][0]["temperature"] == 96


def test_agent_runs_the_tool_sequence_and_returns_source_metadata(monkeypatch):
    class FakeAgent:
        def __init__(self, tools, system_prompt):
            self.tools = tools
            assert "FieldReady" in system_prompt

        def __call__(self, _prompt):
            for registered_tool in self.tools:
                registered_tool()
            return "Check the local forecast and contact Extension for field-specific advice."

    monkeypatch.setattr(fieldready_service, "Agent", FakeAgent)
    monkeypatch.setattr(
        fieldready_service,
        "_fetch_official_conditions",
        lambda *_args: {
            "retrieved_at": "2026-10-31T12:00:00+00:00",
            "alerts": [],
            "alert_status": "available",
            "forecast_status": "available",
            "forecast_periods": [{"temperature": 97, "temperature_unit": "F"}],
            "sources": [
                {"title": "National Weather Service forecast", "url": "https://api.weather.gov/forecast"}
            ],
        },
    )

    result = fieldready_service.FieldReadyService(get_settings()).advise(
        FieldReadyRequest(
            latitude=41.25,
            longitude=-96,
            crop="corn",
            growth_stage="flowering",
        )
    )

    assert "Extension" in result.guidance
    assert result.risk.level == "elevated"
    assert result.actions
    assert result.forecast_status == "available"
    assert any("weather.gov" in source.url for source in result.sources)
    assert any("nifa.usda.gov" in source.url for source in result.sources)


def test_request_rejects_coordinates_outside_pilot_region():
    response = client.post(
        "/api/v1/fieldready/advice",
        json={"latitude": 51, "longitude": -96, "crop": "corn", "growth_stage": "flowering"},
    )

    assert response.status_code == 422


def test_request_rejects_unsupported_crop():
    response = client.post(
        "/api/v1/fieldready/advice",
        json={"latitude": 41, "longitude": -96, "crop": "wheat", "growth_stage": "flowering"},
    )

    assert response.status_code == 422
