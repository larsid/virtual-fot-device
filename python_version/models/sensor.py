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
        # 1. Inicializa os dados do Sensor (define self.id, etc.)
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
        
        # 2. Define o device_id AGORA (antes de iniciar a Thread)
        self.device_id = device_id
        
        # 3. Inicializa a Thread (agora o __hash__ vai funcionar)
        threading.Thread.__init__(self)
        
        self._flow = False
        self._running = False
        self.publisher: Optional[LatencyTrackingMqttClient] = None
        self._stop_event = threading.Event()
        
        self.last_value = random.randint(self.min_value, self.max_value) \
            if self.min_value <= self.max_value else 0
        
        self.name = f"FLOW/{self.device_id}/{self.id}" # Nome da Thread
        self.daemon = True 

    # --- O método __hash__ que você adicionou ---
    def __hash__(self):
        return hash((self.device_id, self.id))

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
        
        while temp_publish > 0:
            if self._stop_event.is_set():
                raise InterruptedException()
                
            values.append(self.get_current_value())
            temp_publish -= self.collection_time
            
            self._stop_event.wait(self.collection_time / 1000.0) 

        return Data(self.device_id, self.id, values)

    def run(self):
        self._running = True
        logger.info(f"Thread do Sensor {self.id} iniciada e aguardando comandos.")

        while self._running:
            if self._flow:
                # Se o publisher ainda não foi injetado (overlap de conexão), a thread não morre, apenas espera!
                if not self.publisher:
                    logger.warning(f"Sensor {self.id} aguardando publisher...")
                    time.sleep(1)
                    continue

                try:
                    data = self._get_data_flow()
                    msg = tatu_wrapper.build_flow_message_response(
                        self.device_id, self.id, self.publishing_time,
                        self.collection_time, data.values
                    )
                    topic = tatu_wrapper.build_tatu_response_topic(self.device_id)
                    self.publisher.publish_and_track(topic, self.id, msg)
                    MessageLogController.get_instance().put_data(data)
                except InterruptedException:
                    logger.info(f"Fluxo pausado para o sensor {self.id}")
                except Exception as e:
                    logger.error(f"Erro no fluxo do sensor {self.id}: {e}", exc_info=True)
            else:
                # MODO HIBERNAÇÃO: Karaf mandou 0,0 ou mandou parar. A thread dorme, mas continua viva.
                time.sleep(0.5)
        
        logger.info(f"Sensor {self.id} desligado definitivamente.")

    def start_flow(self, new_collect: int = -1, new_publish: int = -1):
        if new_collect >= 1 and new_publish >= 1:
            self.collection_time = new_collect
            self.publishing_time = new_publish
        elif self.collection_time <= 0 or self.publishing_time <= 0:
            logger.warning(f"Sensor {self.id} recebeu fluxo 0, entrando em modo de pausa.")
            self.stop_flow()
            return

        self._stop_event.clear()
        self._flow = True
        
        if not self.is_alive(): 
            try:
                self.start() 
            except RuntimeError:
                logger.error(f"Tentativa de reiniciar thread morta no sensor {self.id}")
        else:
            logger.info(f"Sensor {self.id} resumindo fluxo existente.")


    def pause_flow(self):
        if self.is_alive() and self._running:
            self._flow = False # APENAS ENTRA EM HIBERNAÇÃO (A thread continua viva!)
            self._stop_event.set() 
            logger.info(f"Sinal de pausa (hibernação) acionado para o sensor {self.id}")

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
        base_sensor = Sensor(id="NullSensor", type="NullType", collection_time=0, publishing_time=0, min_value=0, max_value=0, delta=0)
        super().__init__("NullDevice", base_sensor)

    def start_flow(self, new_collect: int = -1, new_publish: int = -1):
        logger.warning("Tentativa de iniciar fluxo em NullFoTSensor")
    
    def stop_flow(self):
        pass

    def pause_flow(self):
        pass

NULL_FOT_SENSOR = _NullFoTSensor()