"""Helper functions to convert devices to/from JSON structures."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import List

from ..models.device import Device
from ..models.sensor import Sensor
from . import sensor_wrapper


INVALID_DEVICE = "INVALID_DEVICE"


def get_all_devices(devices: Sequence[Mapping[str, object]] | str | None) -> List[Device]:
    """Return ``Device`` instances for each entry in ``devices``."""

    if devices is None or devices == "":
        return []

    if isinstance(devices, str):
        import json

        data = json.loads(devices)
        if not isinstance(data, list):
            return []
        parsed = [item for item in data if isinstance(item, Mapping)]
    else:
        parsed = [item for item in devices if isinstance(item, Mapping)]

    return [to_device(mapping) for mapping in parsed]


def to_device(device: Mapping[str, object] | str) -> Device:
    """Create a :class:`Device` instance from ``device``."""

    if isinstance(device, str):
        import json

        data = json.loads(device)
        if not isinstance(data, Mapping):
            raise TypeError("Device JSON precisa representar um objeto")
        device_mapping = data
    else:
        device_mapping = device

    sensors_data = device_mapping.get("sensors", [])
    sensors: Iterable[Sensor]
    if isinstance(sensors_data, str) or isinstance(sensors_data, Sequence):
        sensors = sensor_wrapper.get_all_sensors(sensors_data)  # type: ignore[arg-type]
    else:
        sensors = []

    return Device(
        id=str(device_mapping.get("id", INVALID_DEVICE)),
        longitude=float(device_mapping.get("longitude", 0)),
        latitude=float(device_mapping.get("latitude", 0)),
        sensors=list(sensors),
    )


def to_json(device: Device) -> str:
    """Return the JSON string representation of ``device``."""

    return sensor_wrapper.json_dumps(to_json_object(device))


def to_json_object(device: Device) -> dict:
    """Return a JSON-serialisable dictionary for ``device``."""

    return {
        "id": device.id,
        "latitude": device.latitude,
        "longitude": device.longitude,
        "sensors": sensor_wrapper.get_all_json_object_sensors(device.sensors),
    }


__all__ = [
    "get_all_devices",
    "to_device",
    "to_json",
    "to_json_object",
]
