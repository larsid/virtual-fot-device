"""Helper functions to convert sensors to/from JSON structures."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import List

from ..models.sensor import Sensor


def get_all_sensors(sensors: Sequence[Mapping[str, object]] | str | None) -> List[Sensor]:
    """Return ``Sensor`` instances for every entry in ``sensors``."""

    parsed: Sequence[Mapping[str, object]]
    if sensors is None or sensors == "":
        return []
    if isinstance(sensors, str):
        import json

        data = json.loads(sensors)
        if isinstance(data, list):
            parsed = [item for item in data if isinstance(item, dict)]  # type: ignore[assignment]
        else:
            return []
    else:
        parsed = [item for item in sensors if isinstance(item, Mapping)]

    return [to_sensor(mapping) for mapping in parsed]


def get_all_json_sensors(sensors: Iterable[Sensor] | None) -> List[str]:
    """Return the JSON representation for every sensor."""

    return [to_json(sensor) for sensor in sensors or []]


def get_all_json_object_sensors(sensors: Iterable[Sensor] | None) -> List[dict]:
    """Return JSON serialisable dictionaries for the provided sensors."""

    return [to_json_object(sensor) for sensor in sensors or []]


def to_sensor(sensor: Mapping[str, object] | str) -> Sensor:
    """Create a ``Sensor`` from a mapping or JSON string."""

    if isinstance(sensor, str):
        import json

        data = json.loads(sensor)
        if not isinstance(data, Mapping):
            raise TypeError("Sensor JSON precisa representar um objeto")
        sensor_mapping = data
    else:
        sensor_mapping = sensor

    return Sensor(
        id=str(sensor_mapping.get("id", "INVALID_SENSOR")),
        type=str(sensor_mapping.get("type", "INVALID_SENSOR")),
        collection_time=int(sensor_mapping.get("collection_time", 0)),
        publishing_time=int(sensor_mapping.get("publishing_time", 0)),
        min_value=int(sensor_mapping.get("min_value", Sensor.DEFAULT_MIN_VALUE)),
        max_value=int(sensor_mapping.get("max_value", Sensor.DEFAULT_MAX_VALUE)),
        delta=int(sensor_mapping.get("delta", Sensor.DEFAULT_DELTA)),
    )


def to_json(sensor: Sensor) -> str:
    """Return the JSON string representing ``sensor``."""

    return json_dumps(to_json_object(sensor))


def to_json_object(sensor: Sensor) -> dict:
    """Return a dictionary representation of ``sensor`` compatible with the Java implementation."""

    return {
        "id": sensor.id,
        "type": sensor.type,
        "collection_time": sensor.collection_time,
        "publishing_time": sensor.publishing_time,
    }


def json_dumps(obj: object) -> str:
    """Serialise ``obj`` ensuring separators match the Java JSON output style."""

    import json

    return json.dumps(obj, separators=(",", ":"))


__all__ = [
    "get_all_sensors",
    "get_all_json_sensors",
    "get_all_json_object_sensors",
    "to_sensor",
    "to_json",
    "to_json_object",
]
