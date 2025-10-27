import json
import logging
from enum import Enum
from typing import Any, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.device import FoTDevice

logger = logging.getLogger(__name__)

class TATUMethod(Enum):
    GET = "GET"
    FLOW = "FLOW"
    SET = "SET"
    POST = "POST"
    EVT = "EVT"
    CONNECT = "CONNECT"
    CONNACK = "CONNACK"
    INVALID = "INVALID"

class TATUMessage:
    """
    Analisa uma mensagem TATU no formato 'METODO ALVO {CONTEUDO_JSON}'
    ou 'METODO ALVO'
    """
    def __init__(self, payload: str):
        self.raw_payload = payload
        self.method: TATUMethod = TATUMethod.INVALID
        self.target: str = ""
        self.content: str = ""
        
        try:
            # Tenta extrair o método (a primeira palavra)
            parts = payload.strip().split(' ', 1)
            self.method = TATUMethod(parts[0].upper())

            if len(parts) == 1:
                # Nenhuma outra parte (ex: um método sem argumentos)
                return

            remaining_payload = parts[1]

            if self.method in [TATUMethod.CONNACK]:
                # Formato: METHOD {JSON}
                # O "remaining_payload" é o JSON
                self.content = remaining_payload
            
            else:
                # Formato: METHOD TARGET CONTENT
                # (onde CONTENT pode ter espaços)
                # Ex: "VALUE sensorName" ou "SET brokerMqtt {JSON}"
                target_parts = remaining_payload.split(' ', 1)
                self.target = target_parts[0] # "VALUE" ou "brokerMqtt"
                if len(target_parts) == 2:
                    self.content = target_parts[1] # "sensorName" ou "{JSON}"
                    
        except (ValueError, IndexError):
            logger.warning(f"Não foi possível analisar a mensagem TATU: {payload}")



    def is_response(self) -> bool:
        return self.method == TATUMethod.CONNACK

    def get_message_content(self) -> str:
        return self.content

    def get_target(self) -> str:
        return self.target

# --- Funções de Tópico ---

def build_tatu_topic(device_id: str) -> str:
    return f"dev/{device_id}"

def build_tatu_response_topic(device_id: str) -> str:
    return f"dev/{device_id}/RES"

def get_connection_topic() -> str:
    return "dev/CONNECTION"

def get_connection_topic_response() -> str:
    return "dev/CONNECTION/RES"

# --- Funções de Construção de Mensagem ---

def build_connect_message(device: 'FoTDevice', ip: str, timeout: float) -> str:
    """
    Constrói a mensagem CONNECT com base no README.
    """
    sensors_list = [sensor.to_dict() for sensor in device.get_sensors()]
    msg = {
        "HEADER": {"NAME": device.name, "SOURCE_IP": ip},
        "DEVICE": {
            "id": device.id,
            "sensors": sensors_list,
            "longitude": device.longitude,
            "latitude": device.latitude
        },
        "TIME_OUT": timeout
    }
    return f"CONNECT VALUE BROKER {json.dumps(msg)}"

def build_flow_message_response(device_id: str, sensor_id: str, publish_time: int, collect_time: int, values: List[Any]) -> str:
    """
    Constrói uma mensagem de fluxo de dados.
    Baseado em FoTSensor.java, parece ser uma mensagem POST.
    """
    content = {
        "deviceId": device_id,
        "sensorId": sensor_id,
        "publish": publish_time,
        "collect": collect_time,
        "values": values
    }
    # O formato "POST VALUE {sensor_id} {json}" é uma suposição
    # baseada no formato de request.
    return f"POST VALUE {sensor_id} {json.dumps(content)}"


def build_get_message_response(device_id: str, sensor_id: str, value: Any) -> str:
    """
    Constrói uma resposta para um GET.
    DefaultFlowCallback.java chama isso de 'jsonResponse'.
    Publicado no tópico /RES.
    """
    # A implementação Java sugere que a resposta é apenas o payload JSON,
    # não uma mensagem TATU completa.
    return json.dumps({"deviceId": device_id, "sensorId": sensor_id, "value": value})
