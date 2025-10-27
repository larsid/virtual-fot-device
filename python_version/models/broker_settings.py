from dataclasses import dataclass, field
from typing import Optional

# Usamos dataclass(frozen=True) para tornar a classe imutável e "hasheável",
# similar ao comportamento do .hashCode() e .equals() em Java.
@dataclass(frozen=True)
class BrokerSettings:
    url: str
    port: int
    device_id: str
    username: str = ""
    password: str = ""

    @property
    def uri(self) -> str:
        return f"{self.url}:{self.port}"

class BrokerSettingsBuilder:
    def __init__(self):
        self._device_id: Optional[str] = None
        self._broker_ip: Optional[str] = None
        self._port: Optional[str] = None
        self._username: Optional[str] = None
        self._password: Optional[str] = None

    def device_id(self, device_id: str) -> 'BrokerSettingsBuilder':
        if self._device_id is None and device_id:
            self._device_id = device_id
        return self

    def set_broker_ip(self, broker_ip: str) -> 'BrokerSettingsBuilder':
        self._broker_ip = broker_ip
        return self

    def set_port(self, port: str) -> 'BrokerSettingsBuilder':
        self._port = port
        return self

    def set_username(self, username: str) -> 'BrokerSettingsBuilder':
        self._username = username
        return self

    def set_password(self, password: str) -> 'BrokerSettingsBuilder':
        self._password = password
        return self

    def build(self) -> BrokerSettings:
        device_id = self._device_id or "VIRTUAL_FOT_DEVICE"
        if not self._broker_ip:
            broker_ip = "localhost" # Padrão limpo
        else:
            # Remove qualquer prefixo de protocolo que o usuário possa ter digitado
            broker_ip = self._broker_ip.replace("tcp://", "").replace("udp://", "")


        port = int(self._port or "1883")
        username = self._username or ""
        password = self._password or ""

        return BrokerSettings(
            url=broker_ip,
            port=port,
            device_id=device_id,
            username=username,
            password=password
        )
