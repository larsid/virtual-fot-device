import threading
import time
import random
import logging
from dataclasses import dataclass, field
#from typing import List, Optional, Any, Dict, Generic, TypeVar
from util import tatu
from mqtt.client import LatencyTrackingMqttClient
from controllers.persistense import MessageLogController
from models.data import Data
from typing import List, Optional, Any, Dict
logger = logging.getLogger(__name__)
#T = TypeVar('T')

@dataclass(eq=False)
class Sensor:
    """Classe base para um sensor, baseada nos parâmetros do super() em FoTSensor.java"""
    id: str
    type: str
    collection_time: int
    publishing_time: int
    min_value: int
    max_value: int
    delta: int

    def to_dict(self) -> Dict[str, Any]:
        """Necessário para a serialização no CONNECT"""
        return {
            "id": self.id,
            "type": self.type,
            "collection_time": self.collection_time,
            "publishing_time": self.publishing_time,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "delta": self.delta
        }



class FoTSensor(Sensor, threading.Thread):
    
    def __init__(self, device_id: str, base_sensor: Sensor):
        Sensor.__init__(
            self,
            base_sensor.id,
            base_sensor.type,
            base_sensor.collection_time,
            base_sensor.publishing_time,
            base_sensor.min_value,
            base_sensor.max_value,
            base_sensor.delta
        )
        threading.Thread.__init__(self)
        
        self.device_id = device_id
        self._flow = False
        self._running = False
        self.publisher: Optional[LatencyTrackingMqttClient] = None
        self._stop_event = threading.Event()
        
        self.last_value = random.randint(self.min_value, self.max_value) \
            if self.min_value <= self.max_value else 0
        
        self.name = f"FLOW/{self.device_id}/{self.id}" # Nome da Thread
        self.daemon = True # Threads daemon são encerradas quando o principal termina

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
            if self._stop_event.is_set(): # Verifica se a thread foi parada
                raise InterruptedException()
                
            values.append(self.get_current_value())
            temp_publish -= self.collection_time
            
            # Em Python, time.sleep() é bloqueante, mas como estamos em
            # nossa própria thread, isso é aceitável.
            # O 'wait' do Event permite ser interrompido.
            self._stop_event.wait(self.collection_time / 1000.0) # Espera em segundos

        return Data(self.device_id, self.id, values)

    def run(self):
        if not self.publisher:
            logger.error(f"Sensor {self.id} não pode iniciar o fluxo sem um publisher.")
            return

        topic = tatu.build_tatu_response_topic(self.device_id)
        self._flow = True
        self._running = True
        logger.info(f"Sensor {self.id} iniciando fluxo (Coleta: {self.collection_time}ms, Pub: {self.publishing_time}ms)")

        while not self._stop_event.is_set() and self._flow:
            try:
                data = self._get_data_flow()
                
                msg = tatu.build_flow_message_response(
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

        if not self.is_alive(): # Verifica se a thread já foi iniciada
            self._stop_event.clear()
            self.start() # Inicia a thread (chama o run())
        else:
            # Se a thread já está rodando (talvez de um 'pause'), apenas reinicia
            self._stop_event.clear()
            self._flow = True
            logger.info(f"Sensor {self.id} resumindo fluxo.")


    def pause_flow(self):
        """Interrompe a coleta de dados, mas mantém a thread viva."""
        if self.is_alive() and self._running:
            self._running = False
            self._stop_event.set() # Sinaliza para o 'wait' parar

    def stop_flow(self):
        """Para permanentemente o fluxo e a thread."""
        if self.is_alive():
            self._flow = False
            self._running = False
            self._stop_event.set() # Sinaliza para a thread parar
            logger.info(f"Sinal de parada enviado para o sensor {self.id}")

class InterruptedException(Exception):
    """Exceção customizada para simular a InterruptedException do Java."""
    pass


class _NullFoTSensor(FoTSensor):
    """Implementação Singleton do NullFoTSensor"""
    def __init__(self):
        base_sensor = Sensor("NullSensor", "NullType", 0, 0, 0, 0, 0)
        super().__init__("NullDevice", base_sensor)

    def start_flow(self, new_collect: int = -1, new_publish: int = -1):
        logger.warning("Tentativa de iniciar fluxo em NullFoTSensor")
    
    def stop_flow(self):
        pass

    def pause_flow(self):
        pass

# Instância Singleton, como em Java (NullFoTSensor.getInstance())
NULL_FOT_SENSOR = _NullFoTSensor()
