import threading
import time
import random
import logging
from typing import Optional, List
from extended_tatu_wrapper import Sensor  # Importa o Sensor oficial
from extended_tatu_wrapper.utils import tatu_wrapper # Importa o wrapper oficial
from controllers.persistense import MessageLogController
from mqtt.client import LatencyTrackingMqttClient
from models.data import Data # Nosso modelo de dados continua o mesmo

logger = logging.getLogger(__name__)

class FoTSensor(Sensor, threading.Thread):
    
    def __init__(self, device_id: str, base_sensor: Sensor):
        # Inicializa a classe base 'Sensor' oficial
        Sensor.__init__(
            self,
            id=base_sensor.id,
            type=base_sensor.type,
            collection_time=base_sensor.collection_time,
            publishing_time=base_sensor.publishing_time,
            min_value=base_sensor.min_value,
            max_value=base_sensor.max_value,
            delta=base_sensor.delta
        )
        # Inicializa a classe base 'Thread'
        threading.Thread.__init__(self)
        
        self.device_id = device_id
        self._flow = False
        self._running = False
        self.publisher: Optional[LatencyTrackingMqttClient] = None
        self._stop_event = threading.Event()
        
        self.last_value = random.randint(self.min_value, self.max_value) \
            if self.min_value <= self.max_value else 0
        
        self.name = f"FLOW/{self.device_id}/{self.id}" # Nome da Thread
        self.daemon = True 

    def set_publisher(self, publisher: LatencyTrackingMqttClient):
        self.publisher = publisher

    def is_flow(self) -> bool:
        return self._flow

    def is_running(self) -> bool:
        return self._running

    def get_current_value(self) -> int:
        variation = self.delta * (1 if random.random() < 0.5 else -1)
        self.last_value = min(self.max_value, max(self.min_value, self.last_value + variation))
        return self.last_value

    def _get_data_flow(self) -> Data[int]:
        values: List[int] = []
        temp_publish = self.publishing_time
        
        while temp_publish >= 0:
            if self._stop_event.is_set():
                raise InterruptedException()
                
            values.append(self.get_current_value())
            temp_publish -= self.collection_time
            
            self._stop_event.wait(self.collection_time / 1000.0) 

        return Data(self.device_id, self.id, values)

    def run(self):
        if not self.publisher:
            logger.error(f"Sensor {self.id} não pode iniciar o fluxo sem um publisher.")
            return

        # Usa a função oficial do wrapper
        topic = tatu_wrapper.build_tatu_response_topic(self.device_id)
        self._flow = True
        self._running = True
        logger.info(f"Sensor {self.id} iniciando fluxo (Coleta: {self.collection_time}ms, Pub: {self.publishing_time}ms)")

        while not self._stop_event.is_set() and self._flow:
            try:
                data = self._get_data_flow()
                
                # Usa a função oficial do wrapper
                msg = tatu_wrapper.build_flow_message_response(
                    self.device_id, self.id, self.publishing_time,
                    self.collection_time, data.values
                )
                
                self.publisher.publish_and_track(topic, self.id, msg)
                MessageLogController.get_instance().put_data(data)
                
            except InterruptedException:
                logger.info(f"Fluxo interrompido para o sensor {self.id}")
                self._running = False
            except Exception as e:
                logger.error(f"Erro no fluxo do sensor {self.id}: {e}", exc_info=True)
                self._running = False
        
        self._running = False
        self._flow = False
        logger.info(f"Sensor {self.id} parou o fluxo.")

    def start_flow(self, new_collect: int = -1, new_publish: int = -1):
        if new_collect >= 1 and new_publish >= 1:
            self.collection_time = new_collect
            self.publishing_time = new_publish
        elif self.collection_time <= 0 or self.publishing_time <= 0:
            logger.warning(f"Sensor {self.id} não pode iniciar o fluxo com tempos <= 0")
            self.stop_flow()
            return

        if not self.is_alive(): 
            self._stop_event.clear()
            self.start() 
        else:
            self._stop_event.clear()
            self._flow = True
            logger.info(f"Sensor {self.id} resumindo fluxo.")


    def pause_flow(self):
        if self.is_alive() and self._running:
            self._running = False
            self._stop_event.set() 

    def stop_flow(self):
        if self.is_alive():
            self._flow = False
            self._running = False
            self._stop_event.set() 
            logger.info(f"Sinal de parada enviado para o sensor {self.id}")

class InterruptedException(Exception):
    pass


class _NullFoTSensor(FoTSensor):
    def __init__(self):
        # Cria um Sensor base oficial
        base_sensor = Sensor("NullSensor", "NullType", 0, 0, 0, 0, 0)
        super().__init__("NullDevice", base_sensor)

    def start_flow(self, new_collect: int = -1, new_publish: int = -1):
        logger.warning("Tentativa de iniciar fluxo em NullFoTSensor")
    
    def stop_flow(self):
        pass

    def pause_flow(self):
        pass

NULL_FOT_SENSOR = _NullFoTSensor()