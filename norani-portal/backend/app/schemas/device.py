"""Pydantic schemas for device endpoints."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DeviceTypeOut(BaseModel):
    id: str
    name: str
    manufacturer: str | None
    model: str | None
    region: str
    description: str | None

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    device_type_id: str
    dev_eui: str = Field(min_length=16, max_length=23)  # allow colons/spaces, we normalize
    join_eui: str | None = "0000000000000000"
    location_name: str | None = Field(default=None, max_length=500)
    location_lat: float | None = Field(default=None, ge=-90, le=90)
    location_lon: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("dev_eui")
    @classmethod
    def normalize_dev_eui(cls, v: str) -> str:
        # Strip colons, spaces, dashes; lowercase
        v = v.lower().replace(":", "").replace(" ", "").replace("-", "")
        if len(v) != 16:
            raise ValueError("DevEUI must be 16 hex characters")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("DevEUI must contain only hex characters")
        return v

    @field_validator("join_eui")
    @classmethod
    def normalize_join_eui(cls, v: str | None) -> str:
        if not v:
            return "0000000000000000"
        v = v.lower().replace(":", "").replace(" ", "").replace("-", "")
        if len(v) != 16:
            raise ValueError("JoinEUI must be 16 hex characters")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("JoinEUI must contain only hex characters")
        return v


class DeviceOut(BaseModel):
    id: str
    dev_eui: str
    join_eui: str
    name: str
    location_name: str | None
    location_lat: float | None
    location_lon: float | None
    status: str
    last_seen_at: datetime | None
    created_at: datetime
    device_type: DeviceTypeOut

    class Config:
        from_attributes = True


class DeviceCreatedResponse(DeviceOut):
    """Response when a device is just created — includes plaintext AppKey for sticker."""
    app_key: str  # ONLY returned at creation time
    sticker_url: str


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location_name: str | None = Field(default=None, max_length=500)
    location_lat: float | None = Field(default=None, ge=-90, le=90)
    location_lon: float | None = Field(default=None, ge=-180, le=180)
    status: str | None = None


class DeviceMeasurement(BaseModel):
    """A single time-series data point from InfluxDB."""
    timestamp: datetime
    field: str
    value: float


class DeviceListResponse(BaseModel):
    items: list[DeviceOut]
    total: int
    page: int
    page_size: int
