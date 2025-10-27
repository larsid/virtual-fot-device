"""Representation of a TATU device."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from .sensor import Sensor


@dataclass(slots=True)
class Device:
    """Represents a device that exposes sensors via the TATU protocol."""

    id: str
    latitude: float
    longitude: float
    sensors: List[Sensor] = field(default_factory=list)

    def __post_init__(self) -> None:
        # ensure an independent copy of the provided sensors list
        self.sensors = list(self.sensors)

    def get_sensor_by_id(self, sensor_id: str) -> Optional[Sensor]:
        """Return the first sensor that matches ``sensor_id`` if present."""

        return next((sensor for sensor in self.sensors if sensor.id == sensor_id), None)

    @classmethod
    def from_iterable(
        cls, *, id: str, latitude: float, longitude: float, sensors: Iterable[Sensor] | None = None
    ) -> "Device":
        """Create a device from the provided iterable of sensors."""

        sensor_list = list(sensors or [])
        return cls(id=id, latitude=latitude, longitude=longitude, sensors=sensor_list)


__all__ = ["Device"]
