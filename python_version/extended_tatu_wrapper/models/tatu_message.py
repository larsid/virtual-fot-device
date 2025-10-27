"""Representation of TATU protocol messages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..enums import ExtendedTATUMethods
from ..utils import tatu_wrapper


@dataclass(slots=True)
class TATUMessage:
    """Wrap a TATU message and expose convenient accessors."""

    raw_message: str
    method: ExtendedTATUMethods = field(init=False)
    target: str = field(init=False)
    _content: Optional[str] = field(init=False, default=None)
    is_response: bool = field(init=False)

    def __post_init__(self) -> None:
        method_name = tatu_wrapper.get_method(self.raw_message)
        try:
            self.method = ExtendedTATUMethods(method_name)
        except ValueError:
            self.method = ExtendedTATUMethods.INVALID
        self.is_response = tatu_wrapper.is_tatu_response(self.raw_message)
        self.target = self._extract_target(self.raw_message)
        self._content = self._extract_content(self.raw_message)

    @classmethod
    def from_payload(cls, payload: bytes) -> "TATUMessage":
        """Create a message instance from raw byte payloads."""

        return cls(payload.decode())

    @property
    def content(self) -> str:
        """Return the parsed message content if any, otherwise an empty string."""

        return self._content or ""

    def _extract_target(self, message: str) -> str:
        if not self.is_response:
            return tatu_wrapper.get_sensor_id_by_tatu_request(message)
        return tatu_wrapper.get_sensor_id_by_tatu_answer(message)

    def _extract_content(self, message: str) -> Optional[str]:
        new_msg = message.replace("\\", "")
        if self.is_response:
            if tatu_wrapper.is_valid_tatu_answer(new_msg):
                return new_msg
        elif self.method in {ExtendedTATUMethods.FLOW, ExtendedTATUMethods.SET, ExtendedTATUMethods.CONNECT}:
            brace_index = new_msg.find("{")
            if brace_index != -1:
                return new_msg[brace_index:]
        return ""

    def __str__(self) -> str:  # pragma: no cover - convenience
        return (
            '{"isResponse": %s, "message": "%s", "messageContent": "%s", "sensor": "%s", "method": "%s"}'
            % (
                str(self.is_response).lower(),
                self.raw_message,
                self.content,
                self.target,
                self.method.value,
            )
        )


__all__ = ["TATUMessage"]
