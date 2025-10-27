import paho.mqtt.client as mqtt
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from config import ExperimentConfig
from controllers.api_controller import LatencyApiController, LatencyRecord

logger = logging.getLogger(__name__)

@dataclass
class FlightMessageInfo:
    """Substitui FlightMessageInfo.java"""
    sensor_id: str
    message: str
    timestamp: int = field(default_factory=time.monotonic_ns)

    def get_elapsed_time_since_sent(self) -> int:
        # Em nanossegundos
        return time.monotonic_ns() - self.timestamp

class LatencyTrackingMqttClient(mqtt.Client):

    def __init__(self, client_id: str, broker_ip: str, config: ExperimentConfig):
        super().__init__(client_id=client_id)
        self.in_flight_messages: Dict[int, FlightMessageInfo] = {}
        
        # Configura o LatencyApiController
        # (Em Python, é mais comum injetar dependências do que usar singletons)
        self.latency_api: LatencyApiController = LatencyApiController(config)
        self.latency_api.start()
        
        self.device_id = client_id.replace("_CLIENT", "")
        self.broker_ip = broker_ip
        self.config = config

        self.on_publish = self._on_publish_callback
        self.on_connect = self._on_connect_callback

    def _on_connect_callback(self, client, userdata, flags, rc):
        """
        Callback para quando a conexão é estabelecida.
        Usamos isso para implementar o log de IP do LoggingSocketFactory.java
        """
        if rc == 0:
            try:
                sock = self.socket()
                local_ip, local_port = sock.getsockname()
                remote_ip, remote_port = sock.getpeername()
                logger.info(
                    f"Device {self.device_id} established MQTT connection "
                    f"{local_ip}:{local_port} -> {remote_ip}:{remote_port}"
                )
            except Exception as e:
                logger.warning(f"Não foi possível registrar o IP da conexão: {e}")
        else:
            logger.error(f"Falha ao conectar ao broker: {mqtt.connack_string(rc)}")


    def _on_publish_callback(self, client: mqtt.Client, userdata: Any, mid: int):
        """
        Este callback é acionado quando uma mensagem com QoS > 0 é
        publicada (deliveryComplete).
        """
        self.calculate_rtt(mid)

    def publish_and_track(self, topic: str, sensor_id: str, message: str, qos: int = 2):
        """
        Publica uma mensagem e rastreia seu tempo de voo.
        """
        msg_info = self.publish(topic, message, qos=qos)
        
        if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
            flight_info = FlightMessageInfo(sensor_id, message)
            self.in_flight_messages[msg_info.mid] = flight_info
        else:
            logger.warning(f"Falha ao publicar mensagem no tópico {topic} (rc: {msg_info.rc})")

    def calculate_rtt(self, mid: int):
        """
        Calcula o RTT quando a mensagem é confirmada.
        """
        if mid not in self.in_flight_messages:
            logger.info(f"Mensagem com mid {mid} não encontrada para rastreamento de RTT.")
            return

        message_info = self.in_flight_messages.pop(mid)
        
        # Latência em nanossegundos, convertida para milissegundos para o record
        rtt_ns = message_info.get_elapsed_time_since_sent()
        rtt_ms = rtt_ns / 1_000_000 # Converte nanos para milis

        record = LatencyRecord(
            deviceID=self.device_id,
            sensorId=message_info.sensor_id,
            brokerIp=self.broker_ip,
            experiment=self.config.exp_num,
            type=self.config.exp_type,
            level=self.config.exp_level,
            latency=rtt_ms,
            message=message_info.message
        )
        self.latency_api.put_latency_record(record)
