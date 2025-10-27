import logging
import random
from typing import List, Optional
from extended_tatu_wrapper import Device, Sensor # Importa o Device e Sensor oficiais
from extended_tatu_wrapper.utils import tatu_wrapper # Importa o wrapper oficial
from models.sensor import FoTSensor # Importa nosso FoTSensor (que herda de Sensor)
from models.broker_settings import BrokerSettings
from config import ExperimentConfig
from mqtt.client import LatencyTrackingMqttClient
from mqtt.callbacks import DefaultFlowCallback

logger = logging.getLogger(__name__)

# Nossa classe FoTDevice agora herda da classe Device oficial
class FoTDevice(Device):
    
    def __init__(self, name: str, sensors: List[Sensor], config: ExperimentConfig):
        # Inicializa a classe base 'Device' oficial
        Device.__init__(
            self,
            id=name,
            sensors=sensors,
            latitude=random.uniform(-90.0, 90.0),
            longitude=random.uniform(-180.0, 180.0)
        )
        
        # Converte os Sensores base em FoTSensores (que são Threads)
        self.fot_sensors = [FoTSensor(self.id, s) for s in sensors]
        self.config = config
        
        self.client: Optional[LatencyTrackingMqttClient] = None
        self.broker_settings: Optional[BrokerSettings] = None
        
        self.is_updating: bool = False

    def get_fot_sensors(self) -> List[FoTSensor]:
        return self.fot_sensors
        
    def get_fot_sensor_by_sensor_id(self, sensor_id: str) -> Optional[FoTSensor]:
        # get_sensor_by_id() é herdado da classe Device oficial
        fot_sensor = next((fs for fs in self.fot_sensors if fs.id == sensor_id), None)
        return fot_sensor

    def start_flow(self):
        logger.info(f"Dispositivo {self.id}: iniciando fluxo para todos os sensores.")
        for sensor in self._get_flow_sensors():
            sensor.start_flow()

    def pause_flow(self):
        logger.info(f"Dispositivo {self.id}: pausando fluxo para todos os sensores.")
        for sensor in self._get_flow_sensors():
            sensor.pause_flow()

    def stop_flow(self):
        logger.info(f"Dispositivo {self.id}: parando fluxo para todos os sensores.")
        for sensor in self.fot_sensors:
            if sensor.is_running():
                sensor.stop_flow()

    def _get_flow_sensors(self) -> List[FoTSensor]:
        return [s for s in self.fot_sensors if s.is_flow()]

    def connect(self, broker_settings: BrokerSettings):
        logger.info(f"Dispositivo {self.id} conectando a {broker_settings.uri}")
        
        client_id = f"{self.id}_CLIENT"
        self.client = LatencyTrackingMqttClient(client_id, broker_settings.url, self.config)
        self.broker_settings = broker_settings

        default_callback = DefaultFlowCallback(self, self.config)
        self.client.on_message = default_callback.on_message
        self.client.on_disconnect = default_callback.on_disconnect
        
        if broker_settings.username and broker_settings.password:
            self.client.username_pw_set(broker_settings.username, broker_settings.password)

        try:
            self.client.connect(broker_settings.url, broker_settings.port)
            self.client.loop_start()

            # Usa a função oficial do wrapper
            topic = tatu_wrapper.build_tatu_topic(self.id)
            self.client.subscribe(topic, qos=2)
            logger.info(f"Dispositivo {self.id} inscrito no tópico: {topic}")

            for sensor in self.fot_sensors:
                sensor.set_publisher(self.client)

        except Exception as e:
            logger.error(f"Falha ao conectar o dispositivo {self.id}: {e}", exc_info=True)
            if self.client:
                self.client.loop_stop()
            raise

    def update_broker_settings(self, new_broker_settings: BrokerSettings):
        logger.info(f"Dispositivo {self.id} atualizando para o broker: {new_broker_settings.uri}")
        old_broker_settings = self.broker_settings
        old_client = self.client
        
        self.pause_flow()
        
        try:
            self.connect(new_broker_settings)
            
            if old_client:
                logger.info(f"Desconectando do broker antigo: {old_broker_settings.uri}")
                old_client.loop_stop()
                old_client.disconnect()
                
        except Exception as e:
            logger.error(f"Falha ao atualizar para o novo broker. Revertendo... {e}")
            if old_client and old_broker_settings:
                self.connect(old_broker_settings)
            else:
                logger.critical("Falha ao reverter para o broker antigo. Estado inconsistente.")
        
        self.start_flow()
        self.is_updating = False