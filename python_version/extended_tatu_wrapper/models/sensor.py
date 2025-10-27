"""Representation of a TATU sensor entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(slots=True, eq=False)
class Sensor:
    """Represents a sensor that can be published through TATU."""

    DEFAULT_MIN_VALUE: ClassVar[int] = 10
    DEFAULT_MAX_VALUE: ClassVar[int] = 30
    DEFAULT_DELTA: ClassVar[int] = 1

    id: str = ""
    type: str = ""
    collection_time: int = 0
    publishing_time: int = 0
    min_value: int = DEFAULT_MIN_VALUE
    max_value: int = DEFAULT_MAX_VALUE
    delta: int = DEFAULT_DELTA

    def __post_init__(self) -> None:
        if self.min_value > self.max_value:
            raise ValueError(
                "O sensor [id]: %s [type]: %s possui um valor minimo %s maior que o máximo %s."  # noqa: D400
                % (self.id, self.type, self.min_value, self.max_value)
            )


__all__ = ["Sensor"]
