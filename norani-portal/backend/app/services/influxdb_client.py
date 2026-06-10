"""InfluxDB client for querying historical sensor data.

ChirpStack writes uplinks to InfluxDB via its built-in integration. We query
that same bucket to provide historical charts and CSV exports to customers.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class InfluxDBClient:
    """Wrapper around influxdb-client for our specific query patterns."""

    def __init__(self) -> None:
        # Lazy import so the portal still starts without InfluxDB
        try:
            from influxdb_client import InfluxDBClient as _Client
            self._client = _Client(
                url=settings.influxdb_url,
                token=settings.influxdb_token,
                org=settings.influxdb_org,
            )
            self.query_api = self._client.query_api()
            self.available = True
        except Exception as e:
            logger.warning("InfluxDB client unavailable: %s", e)
            self.available = False

    def get_device_measurements(
        self,
        dev_eui: str,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        field: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """Get time-series readings for a device within a time range."""
        if not self.available:
            return []

        if not from_time:
            from_time = datetime.utcnow() - timedelta(hours=24)
        if not to_time:
            to_time = datetime.utcnow()

        field_filter = f'  |> filter(fn: (r) => r._field == "{field}")' if field else ""

        flux = f"""
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: {from_time.isoformat()}Z, stop: {to_time.isoformat()}Z)
  |> filter(fn: (r) => r._measurement == "device_frmpayload_data")
  |> filter(fn: (r) => r.dev_eui == "{dev_eui}")
{field_filter}
  |> limit(n: {limit})
"""

        try:
            tables = self.query_api.query(flux)
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "timestamp": record.get_time(),
                        "field": record.get_field(),
                        "value": float(record.get_value()),
                    })
            return results
        except Exception as e:
            logger.error("InfluxDB query failed: %s", e)
            return []

    def get_latest_reading(self, dev_eui: str) -> Optional[dict]:
        """Get the most recent uplink for a device."""
        if not self.available:
            return None

        flux = f"""
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "device_frmpayload_data")
  |> filter(fn: (r) => r.dev_eui == "{dev_eui}")
  |> last()
"""

        try:
            tables = self.query_api.query(flux)
            data = {}
            timestamp = None
            for table in tables:
                for record in table.records:
                    timestamp = record.get_time()
                    data[record.get_field()] = float(record.get_value())
            if timestamp:
                return {"timestamp": timestamp, "fields": data}
            return None
        except Exception as e:
            logger.error("InfluxDB latest query failed: %s", e)
            return None


# Module-level singleton (lazy-initialised — won't crash if InfluxDB is down)
influx_client = InfluxDBClient()
