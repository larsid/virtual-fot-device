import requests
import logging
import threading
import time
from queue import Queue, Empty
from dataclasses import dataclass, asdict
from typing import List, Optional
from config import ExperimentConfig

logger = logging.getLogger(__name__)

@dataclass
class LatencyRecord:
    deviceID: str
    sensorId: str
    brokerIp: str
    experiment: int
    type: int
    level: int
    latency: float # Em ms
    message: str

class LatencyLoggerApiClient:
    """Substitui LatencyLoggerApiClient.java"""
    def __init__(self, url: str):
        self.url = url
        self.client = requests.Session()
        self.client.headers.update({"Content-Type": "application/json"})

    def post_all_latencies(self, records: List[LatencyRecord]):
        json_payload = [asdict(r) for r in records]
        try:
            response = self.client.post(self.url, json=json_payload)
            response.raise_for_status() # Lança exceção para erros HTTP
            logger.info(f"Enviados {len(records)} registros de latência para a API.")
        except requests.RequestException as e:
            logger.error(f"Falha ao enviar registros de latência para a API: {e}")

class LatencyApiController(threading.Thread):
    """Substitui LatencyApiController.java (Runnable)"""
    def __init__(self, config: ExperimentConfig):
        super().__init__(daemon=True, name="LATENCY_LOGGER_API_WRITER")
        self.api_client = LatencyLoggerApiClient(config.api_url)
        self.buffer: Queue[Optional[LatencyRecord]] = Queue()
        self.buffer_size = config.buffer_size
        self.stop_event = threading.Event()

    def put_latency_record(self, record: LatencyRecord):
        self.buffer.put(record)
    
    def stop(self):
        self.stop_event.set()
        self.buffer.put(None) # Sinal de parada

    def run(self):
        logger.info("Thread LatencyApiController iniciada.")
        latency_lines: List[LatencyRecord] = []
        while not self.stop_event.is_set():
            try:
                record = self.buffer.get(timeout=1.0)
                if record is None: # Sinal de parada
                    break
                
                latency_lines.append(record)
                
                if len(latency_lines) >= self.buffer_size:
                    self.api_client.post_all_latencies(latency_lines)
                    latency_lines.clear()
                    
            except Empty:
                continue # Timeout, volta ao loop
        
        # Envia o restante
        if latency_lines:
            self.api_client.post_all_latencies(latency_lines)
        logger.info("Thread LatencyApiController encerrada.")
