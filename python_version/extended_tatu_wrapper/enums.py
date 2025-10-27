"""Enumerations used by the extended TATU wrapper."""

from __future__ import annotations

from enum import Enum


class ExtendedTATUMethods(str, Enum):
    """Enumeration of valid TATU methods understood by the wrapper."""

    CONNECT = "CONNECT"
    CONNACK = "CONNACK"
    EVT = "EVT"
    FLOW = "FLOW"
    GET = "GET"
    SET = "SET"
    POST = "POST"
    INVALID = "INVALID"

    def __str__(self) -> str:  # pragma: no cover - convenience for printing
        return self.value


__all__ = ["ExtendedTATUMethods"]
