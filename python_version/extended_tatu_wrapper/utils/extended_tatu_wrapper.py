"""Utilities for messages introduced by the extended TATU protocol."""

from __future__ import annotations

from typing import Optional

from ..models.device import Device
from . import device_wrapper
from .tatu_wrapper import TOPIC_BASE, TOPIC_RESPONSE
from .tatu_wrapper import json_dumps as tatu_json_dumps


def get_connection_topic() -> str:
    """Return the topic used to announce device connections."""

    return f"{TOPIC_BASE}CONNECTIONS"


def get_connection_topic_response() -> str:
    """Return the response topic for connection acknowledgements."""

    return f"{get_connection_topic()}{TOPIC_RESPONSE}"


def build_connect_message(device: Device, ip: Optional[str] = None, timeout: Optional[float] = None) -> str:
    """Build a CONNECT VALUE BROKER message for ``device``."""

    header = {"NAME": device.id, "TIMESTAMP": _current_timestamp()}
    if ip is not None:
        header["SOURCE_IP"] = ip

    body = {
        "TIME_OUT": timeout,
        "HEADER": header,
        "DEVICE": device_wrapper.to_json_object(device),
    }
    # Remove null TIME_OUT to match Java behaviour when no timeout provided
    if timeout is None:
        body.pop("TIME_OUT")

    return f"CONNECT VALUE BROKER {tatu_json_dumps(body)}"


def build_connack_message(device_name: str, new_device_name: str, success: bool) -> str:
    """Build a CONNACK response compatible with the Java implementation."""

    response = {
        "METHOD": "CONNACK",
        "CODE": "POST",
        "HEADER": {
            "NAME": device_name,
            "TIMESTAMP": _current_timestamp(),
        },
        "BODY": {
            "NEW_NAME": new_device_name,
            "CAN_CONNECT": success,
        },
    }
    return tatu_json_dumps(response)


def _current_timestamp() -> int:
    import time

    return int(time.time() * 1000)


__all__ = [
    "get_connection_topic",
    "get_connection_topic_response",
    "build_connect_message",
    "build_connack_message",
]
