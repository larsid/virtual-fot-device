"""Core utilities shared across TATU messages."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ..enums import ExtendedTATUMethods

TOPIC_BASE = "dev/"
TOPIC_RESPONSE = "/RES"


def build_tatu_flow_info_message(sensor_id: str, collect_seconds: int, publish_seconds: int) -> str:
    """Return a FLOW INFO message for ``sensor_id``."""

    return _build_tatu_flow(sensor_id, collect_seconds, publish_seconds, "INFO ")


def build_tatu_flow_value_message(sensor_id: str, collect_seconds: int, publish_seconds: int) -> str:
    """Return a FLOW VALUE message for ``sensor_id``."""

    return _build_tatu_flow(sensor_id, collect_seconds, publish_seconds, "VALUE ")


def _build_tatu_flow(sensor_id: str, collect_seconds: int, publish_seconds: int, command: str) -> str:
    return (
        "FLOW "
        f"{command}{sensor_id} "
        f"{{\"collect\":{collect_seconds},\"publish\":{publish_seconds}, \"TIMESTAMP\":{_current_timestamp()}}}"
    )


def build_tatu_topic(device_name: str) -> str:
    """Return the base topic for ``device_name``."""

    return f"{TOPIC_BASE}{device_name}"


def build_tatu_response_topic(device_name: str) -> str:
    """Return the response topic for ``device_name``."""

    return f"{build_tatu_topic(device_name)}{TOPIC_RESPONSE}"


def build_get_message_response(device_name: str, sensor_name: str, value: Any) -> str:
    """Build a JSON response to a GET request."""

    response = {
        "METHOD": "GET",
        "CODE": "POST",
        "HEADER": {
            "NAME": device_name,
            "TIMESTAMP": _current_timestamp(),
        },
        "BODY": {sensor_name: value},
    }
    return json_dumps(response)


def build_flow_message_response(
    device_name: str,
    sensor_name: str,
    publish: int,
    collect: int,
    values: Iterable[Any],
) -> str:
    """Build a JSON FLOW response message."""

    response = {
        "METHOD": "FLOW",
        "CODE": "POST",
        "HEADER": {
            "NAME": device_name,
            "TIMESTAMP": _current_timestamp(),
        },
        "BODY": {
            sensor_name: list(values),
            "FLOW": {"publish": publish, "collect": collect},
        },
    }
    return json_dumps(response)


def is_tatu_response(message: Optional[str]) -> bool:
    """Return ``True`` when ``message`` represents a valid TATU response."""

    return is_valid_message(message) and is_valid_tatu_answer(message or "")


def is_valid_message(message: Optional[str]) -> bool:
    """Heuristically verify whether ``message`` has enough characters to be valid."""

    return bool(message) and len(message or "") > 10


def is_valid_tatu_answer(answer: str) -> bool:
    """Validate if ``answer`` complies with the TATU JSON schema."""

    try:
        json_object = json_loads(answer)
    except ValueError:
        return False

    code = json_object.get("CODE")
    body = json_object.get("BODY")
    return code == "POST" and isinstance(body, dict)


def get_method(message: Optional[str]) -> str:
    """Return the method name encoded in ``message``."""

    if not is_valid_message(message):
        return ExtendedTATUMethods.INVALID.value

    msg = message or ""
    if is_valid_tatu_answer(msg):
        json_object = json_loads(msg)
        return str(json_object.get("METHOD", ExtendedTATUMethods.INVALID.value))
    return msg.split(" ")[0]


def get_device_id_by_tatu_answer(answer: str) -> str:
    json_object = json_loads(answer)
    header = json_object.get("HEADER", {})
    return str(header.get("NAME", ""))


def get_sensor_id_by_tatu_answer(answer: str) -> str:
    json_object = json_loads(answer)
    body = json_object.get("BODY", {})
    for key in body:
        if key != "FLOW":
            return str(key)
    raise KeyError("Nenhum sensor encontrado na resposta TATU")


def get_sensor_id_by_tatu_request(request: str) -> str:
    parts = request.split(" ")
    if len(parts) < 3:
        raise ValueError("Requisição TATU inválida")
    return parts[2]


def get_message_timestamp(message: Optional[str]) -> int:
    if not message or "TIMESTAMP" not in message:
        return -1

    if "FLOW" in message and not is_valid_tatu_answer(message):
        json_object = _get_json_object_from_flow_message(message)
        if json_object is None:
            return -1
        if "TIMESTAMP" in json_object:
            return int(json_object.get("TIMESTAMP", -1))
        header = json_object.get("HEADER", {})
        return int(header.get("TIMESTAMP", -1))

    json_object = json_loads(message)
    header = json_object.get("HEADER", {})
    return int(header.get("TIMESTAMP", -1))


def _get_json_object_from_flow_message(input_message: str) -> Optional[dict]:
    start_index = input_message.find("{")
    if start_index == -1:
        return None
    try:
        return json_loads(input_message[start_index:])
    except ValueError:
        return None


def json_dumps(obj: Any) -> str:
    import json

    return json.dumps(obj, separators=(",", ":"))


def json_loads(data: str) -> dict:
    import json

    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("JSON precisa representar um objeto")
    return value


def _current_timestamp() -> int:
    import time

    return int(time.time() * 1000)


__all__ = [
    "TOPIC_BASE",
    "TOPIC_RESPONSE",
    "build_tatu_flow_info_message",
    "build_tatu_flow_value_message",
    "build_tatu_topic",
    "build_tatu_response_topic",
    "build_get_message_response",
    "build_flow_message_response",
    "is_tatu_response",
    "is_valid_message",
    "is_valid_tatu_answer",
    "get_method",
    "get_device_id_by_tatu_answer",
    "get_sensor_id_by_tatu_answer",
    "get_sensor_id_by_tatu_request",
    "get_message_timestamp",
    "json_dumps",
    "json_loads",
]
