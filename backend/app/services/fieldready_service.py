from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from strands import Agent, tool

from app.config import Settings
from app.models.fieldready import (
    FieldReadyAlert,
    FieldReadyRequest,
    FieldReadyResponse,
    FieldReadyRisk,
    FieldReadySource,
)

logger = logging.getLogger(__name__)

NWS_API = "https://api.weather.gov"
NWS_WEBSITE = "https://www.weather.gov"
EXTENSION_URL = "https://www.nifa.usda.gov/about-nifa/how-we-work/extension"
LIMITATIONS = [
    "This English-language pilot covers the contiguous United States and only corn and soybean.",
    "Weather alerts are official NWS products; forecast screening signals are not official alerts.",
    "No active drought alert found does not mean drought is absent. This pilot does not use U.S. Drought Monitor data.",
    "Guidance is general decision support, not a crop-specific irrigation prescription or a substitute for local Extension or emergency advice.",
]


def _nws_client(contact_email: str | None) -> httpx.Client:
    contact = f" (contact: {contact_email})" if contact_email else ""
    return httpx.Client(
        headers={"User-Agent": f"FieldReady/0.1{contact}", "Accept": "application/geo+json"},
        timeout=12.0,
    )


def _fetch_official_conditions(
    latitude: float, longitude: float, contact_email: str | None
) -> dict[str, Any]:
    point = f"{latitude:.4f},{longitude:.4f}"
    retrieved_at = datetime.now(timezone.utc).isoformat()
    conditions: dict[str, Any] = {
        "retrieved_at": retrieved_at,
        "alerts": [],
        "alert_status": "unavailable",
        "forecast_status": "unavailable",
        "forecast_periods": [],
        "sources": [],
    }

    with _nws_client(contact_email) as client:
        alerts_url = f"{NWS_API}/alerts/active?point={point}"
        try:
            response = client.get(alerts_url)
            response.raise_for_status()
            payload = response.json()
            features = payload.get("features", [])
            conditions["alerts"] = [
                {
                    "event": feature.get("properties", {}).get("event") or "Weather alert",
                    "headline": feature.get("properties", {}).get("headline")
                    or feature.get("properties", {}).get("event")
                    or "Weather alert",
                    "effective": feature.get("properties", {}).get("effective"),
                    "expires": feature.get("properties", {}).get("expires"),
                    "url": feature.get("id") or alerts_url,
                }
                for feature in features
                if isinstance(feature, dict) and isinstance(feature.get("properties"), dict)
            ]
            conditions["alert_status"] = "available"
            conditions["sources"].append({"title": "National Weather Service active alerts", "url": alerts_url})
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("NWS alert lookup failed (%s).", type(exc).__name__)

        points_url = f"{NWS_API}/points/{point}"
        try:
            point_response = client.get(points_url)
            point_response.raise_for_status()
            forecast_url = point_response.json().get("properties", {}).get("forecast")
            parsed_url = urlparse(forecast_url or "")
            if parsed_url.scheme != "https" or parsed_url.hostname != "api.weather.gov":
                raise ValueError("NWS returned an invalid forecast URL.")
            forecast_response = client.get(forecast_url)
            forecast_response.raise_for_status()
            periods = forecast_response.json().get("properties", {}).get("periods", [])
            conditions["forecast_periods"] = [
                {
                    "name": period.get("name"),
                    "temperature": period.get("temperature"),
                    "temperature_unit": period.get("temperatureUnit"),
                    "short_forecast": period.get("shortForecast"),
                }
                for period in periods[:14]
                if isinstance(period, dict)
            ]
            conditions["forecast_status"] = "available"
            conditions["sources"].append({"title": "National Weather Service forecast", "url": forecast_url})
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("NWS forecast lookup failed (%s).", type(exc).__name__)

    return conditions


def _assess_conditions(conditions: dict[str, Any]) -> dict[str, Any]:
    if conditions["alert_status"] == "unavailable" and conditions["forecast_status"] == "unavailable":
        return {
            "level": "unavailable",
            "summary": "Official weather information could not be retrieved. No risk assessment is available.",
            "drought_alert_status": "unavailable",
            "forecast_high_f": None,
        }

    events = [str(alert["event"]).lower() for alert in conditions["alerts"]]
    drought_alert_status = (
        "unavailable"
        if conditions["alert_status"] == "unavailable"
        else "active_alert"
        if any("drought" in event for event in events)
        else "no_active_alert_found"
    )
    relevant_heat_alert = any(
        any(term in event for term in ("heat", "excessive temperature"))
        for event in events
    )
    forecast_highs = [
        float(period["temperature"])
        for period in conditions["forecast_periods"]
        if period.get("temperature_unit") == "F"
        and isinstance(period.get("temperature"), (int, float))
        and period.get("temperature") >= 90
    ]
    forecast_high = max(forecast_highs, default=None)

    if relevant_heat_alert or (forecast_high is not None and forecast_high >= 95):
        level = "elevated"
        summary = "An active NWS heat alert or a forecast high of at least 95°F was found; verify local conditions and guidance."
    elif forecast_high is not None:
        level = "monitor"
        summary = "The forecast includes a high of 90–94°F; monitor official updates and local conditions."
    else:
        level = "no_heat_signal"
        alerts_message = (
            "NWS alert data is unavailable"
            if conditions["alert_status"] == "unavailable"
            else "No NWS heat alert was found"
        )
        forecast_message = (
            "forecast data is unavailable"
            if conditions["forecast_status"] == "unavailable"
            else "no 90°F-plus forecast period was found"
        )
        summary = f"{alerts_message}; {forecast_message}."

    return {
        "level": level,
        "summary": summary,
        "drought_alert_status": drought_alert_status,
        "forecast_high_f": forecast_high,
    }


def _actions_for_conditions(
    conditions: dict[str, Any], risk: dict[str, Any], request: FieldReadyRequest
) -> list[str]:
    if risk["level"] == "unavailable":
        return [
            "Check current conditions and alerts directly with the National Weather Service before making weather-related decisions."
        ]

    actions = [
        "Check with your local Extension office for advice tailored to your field, crop variety, and growth stage before changing irrigation plans.",
        "Follow any active National Weather Service alerts and local water-use restrictions.",
    ]
    if risk["level"] in ("elevated", "monitor"):
        actions.insert(
            0,
            "Recheck the forecast and inspect your field for signs of heat or water stress; this screening does not determine crop water needs.",
        )
    if risk["drought_alert_status"] == "active_alert":
        actions.append("Ask your local Extension office or USDA service center about current drought resources and local options.")
    if request.growth_stage == "flowering":
        actions.append(
            f"For {request.crop} at flowering, request stage-specific guidance from your local Extension office; this pilot does not estimate yield or irrigation thresholds."
        )
    return actions


def _assistant_text(response: Any) -> str:
    message = getattr(response, "message", None)
    if isinstance(message, dict):
        for item in message.get("content", []):
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                return item["text"].strip()
    return str(response).strip()


class FieldReadyService:
    def __init__(self, settings: Settings) -> None:
        self._contact_email = settings.fieldready_contact_email

    def advise(self, request: FieldReadyRequest) -> FieldReadyResponse:
        context: dict[str, Any] = {}

        @tool
        def get_official_conditions() -> str:
            """Retrieve active National Weather Service alerts and the local forecast."""
            context["conditions"] = _fetch_official_conditions(
                request.latitude, request.longitude, self._contact_email
            )
            return json.dumps(context["conditions"])

        @tool
        def assess_crop_stage_risk() -> str:
            """Assess heat and drought alert signals from the retrieved official data."""
            if "conditions" not in context:
                context["conditions"] = {
                    "alert_status": "unavailable",
                    "forecast_status": "unavailable",
                    "alerts": [],
                    "forecast_periods": [],
                    "sources": [],
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                }
            context["risk"] = _assess_conditions(context["conditions"])
            return json.dumps(context["risk"])

        @tool
        def prepare_field_actions() -> str:
            """Provide cautious, general steps grounded in the assessment and local sources."""
            conditions = context.get("conditions", {})
            risk = context.get("risk") or _assess_conditions(conditions)
            context["actions"] = _actions_for_conditions(conditions, risk, request)
            return json.dumps(context["actions"])

        agent = Agent(
            tools=[get_official_conditions, assess_crop_stage_risk, prepare_field_actions],
            system_prompt=(
                "You are FieldReady, an English-language, cautious weather guide for corn and soybean "
                "farmers in the contiguous United States. For every request, call get_official_conditions, "
                "then assess_crop_stage_risk, then prepare_field_actions. Use only tool results for weather "
                "facts and suggested actions. Clearly label official NWS alerts separately from forecast "
                "screening signals. Never say that drought is absent just because no alert was found. Do not "
                "invent alerts, measurements, crop thresholds, irrigation prescriptions, or sources. If data "
                "is unavailable, say so plainly and direct the farmer to official NWS information. Keep the "
                "answer short, use plain English, and mention that advice is general and not a substitute "
                "for local Extension guidance."
            ),
        )
        prompt = (
            f"Prepare a brief field update for {request.crop} at the {request.growth_stage} stage. "
            f"The field coordinates are {request.latitude}, {request.longitude}. "
            "Use the tools in the required order, distinguish alerts from forecasts, and include the "
            "returned action steps and source links."
        )

        try:
            guidance = _assistant_text(agent(prompt))
        except Exception as exc:
            logger.exception("FieldReady agent request failed (%s).", type(exc).__name__)
            raise RuntimeError("The FieldReady agent is temporarily unavailable.") from exc

        if not {"conditions", "risk", "actions"}.issubset(context):
            raise RuntimeError("The FieldReady agent did not complete its required data checks.")

        conditions = context.get("conditions", {})
        risk = context.get("risk") or _assess_conditions(conditions)
        alerts = [FieldReadyAlert(**alert) for alert in conditions.get("alerts", [])]
        sources = [
            FieldReadySource(
                title=source["title"],
                url=source["url"],
                retrieved_at=conditions["retrieved_at"],
            )
            for source in conditions.get("sources", [])
        ]
        if not any(source.url == EXTENSION_URL for source in sources):
            sources.append(
                FieldReadySource(
                    title="USDA National Institute of Food and Agriculture: Extension",
                    url=EXTENSION_URL,
                    retrieved_at=conditions.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                )
            )

        return FieldReadyResponse(
            guidance=guidance,
            risk=FieldReadyRisk(**risk),
            alerts_status=conditions["alert_status"],
            forecast_status=conditions["forecast_status"],
            active_alerts=alerts,
            sources=sources,
            limitations=LIMITATIONS,
        )


def get_fieldready_service() -> FieldReadyService:
    from app.config import get_settings

    return FieldReadyService(get_settings())
