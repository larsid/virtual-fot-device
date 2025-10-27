import time
from dataclasses import dataclass, field
from typing import List, Generic, TypeVar

T = TypeVar('T')

@dataclass
class Data(Generic[T]):
    """Substitui Data.java"""
    device_id: str
    sensor_id: str
    values: List[T]
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))

    def __str__(self) -> str:
        values_str = ",".join(map(str, self.values))
        return f"{self.timestamp},{self.device_id},{self.sensor_id},{values_str}"
