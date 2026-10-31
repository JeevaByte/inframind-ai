from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FieldReadyRequest(BaseModel):
    latitude: float = Field(ge=24, le=50)
    longitude: float = Field(ge=-125, le=-66)
    crop: Literal["corn", "soybean"]
    growth_stage: Literal["seedling", "vegetative", "flowering", "grain_fill"]


class FieldReadyAlert(BaseModel):
    event: str
    headline: str
    effective: str | None = None
    expires: str | None = None
    url: str


class FieldReadySource(BaseModel):
    title: str
    url: str
    retrieved_at: str


class FieldReadyRisk(BaseModel):
    level: Literal["elevated", "monitor", "no_heat_signal", "unavailable"]
    summary: str
    drought_alert_status: Literal["active_alert", "no_active_alert_found", "unavailable"]
    forecast_high_f: float | None = None


class FieldReadyResponse(BaseModel):
    guidance: str
    risk: FieldReadyRisk
    alerts_status: Literal["available", "unavailable"]
    forecast_status: Literal["available", "unavailable"]
    active_alerts: list[FieldReadyAlert]
    sources: list[FieldReadySource]
    limitations: list[str]
