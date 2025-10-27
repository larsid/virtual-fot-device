import threading
import logging
import time
from abc import ABC, abstractmethod
from queue import Queue, Empty
from pathlib import Path
from typing import List, Generic, TypeVar, Optional
from models.data import Data

logger = logging.getLogger(__name__)
T = TypeVar('T')

class FilePersistenceController(ABC, Generic[T]):
    
    _instance = None # Para o padrão Singleton
    
    def __init__(self, default_filename: str):
        if not hasattr(self, '_initialized'): # Evita re-inicialização
            self.buffer_size = 64
            self.can_save_data = False
            self.thread: Optional[threading.Thread] = None
            self.file_name: Optional[Path] = None
            self.buffer: Queue[T] = Queue()
            self.stop_event = threading.Event()
            self._initialized = True
            
    @classmethod
    def get_instance(cls) -> 'FilePersistenceController':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @abstractmethod
    def get_thread_name(self) -> str:
        pass

    @abstractmethod
    def _process_item(self, item: T) -> str:
        """Converte um item do buffer em uma linha de string para o arquivo."""
        pass
        
    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(
                target=self.run, 
                name=self.get_thread_name(),
                daemon=True
            )
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.buffer.put(None) # Adiciona um "None" para acordar a thread
        if self.thread:
            self.thread.join(timeout=5.0)

    def set_can_save_data(self, can_save: bool):
        self.can_save_data = can_save

    def create_and_update_filename(self, file_name: str):
        try:
            exp_dir = Path("exp")
            exp_dir.mkdir(exist_ok=True)
            
            self.file_name = exp_dir / file_name
            
            if not self.file_name.exists():
                self.file_name.touch()
                logger.info(f"Arquivo de log criado: {self.file_name}")
            else:
                logger.info(f"Arquivo de log existente: {self.file_name}")
        
        except IOError as e:
            logger.error(f"Não foi possível criar o arquivo de log {file_name}: {e}")

    def run(self):
        logger.info(f"Thread {self.get_thread_name()} iniciada.")
        lines_to_write: List[str] = []
        
        while not self.stop_event.is_set():
            try:
                # Espera por itens no buffer
                item = self.buffer.get(timeout=1.0)
                
                if item is None: # Sinal de parada
                    break
                    
                lines_to_write.append(self._process_item(item))
                
                if len(lines_to_write) >= self.buffer_size:
                    self._write_lines(lines_to_write)
                    lines_to_write.clear()
                    
            except Empty:
                # Timeout, verifica se é para parar
                continue
            except Exception as e:
                logger.error(f"Erro na thread de persistência: {e}", exc_info=True)
        
        # Escreve o que sobrou no buffer
        if lines_to_write:
            self._write_lines(lines_to_write)
        
        logger.info(f"Thread {self.get_thread_name()} encerrada.")

    def _write_lines(self, lines: List[str]):
        if not self.can_save_data or self.file_name is None:
            return
            
        try:
            with self.file_name.open("a", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")
            logger.info(f"Escritas {len(lines)} linhas em {self.file_name}")
        except IOError as e:
            logger.error(f"Falha ao escrever no arquivo de log {self.file_name}: {e}")

class MessageLogController(FilePersistenceController[Data]):
    
    _instance = None # Singleton
    
    def __init__(self):
        super().__init__("messages_log.csv")

    def get_thread_name(self) -> str:
        return "MESSAGE_LOG_WRITER"

    def put_data(self, data: Data):
        if self.can_save_data:
            self.buffer.put(data)

    def _process_item(self, item: Data) -> str:
        return str(item)

# LatencyLogController seguiria o mesmo padrão...
