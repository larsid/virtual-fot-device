import sys
import json
import logging
import time
from pathlib import Path
from typing import List
from models.sensor import Sensor
from models.device import FoTDevice
from models.broker_settings import BrokerSettingsBuilder
from config import DeviceConfig, ExperimentConfig
from mqtt.callbacks import BrokerUpdateCallback
from controllers.persistense import MessageLogController
# Importe outros controllers se necessário (LatencyLogController, LatencyApiController)

# Configuração básica do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_sensors(file_name: str) -> List[Sensor]:
    """
    Lê a definição dos sensores do arquivo JSON.
    Em um projeto real, o 'sensors.json' estaria em um local
    de 'resources'.
    """
    try:
        # Tenta encontrar o 'sensors.json' relativo a este arquivo
        json_path = Path(__file__).parent / file_name
        with json_path.open('r', encoding='utf-8') as f:
            sensors_data = json.load(f)
            
        sensors = []
        for s_data in sensors_data:
            sensors.append(Sensor(
                id=s_data.get("id"),
                type=s_data.get("type"),
                collection_time=s_data.get("collection_time"),
                publishing_time=s_data.get("publishing_time"),
                min_value=s_data.get("min_value"),
                max_value=s_data.get("max_value"),
                delta=s_data.get("delta")
            ))
        return sensors
        
    except FileNotFoundError:
        logger.error(f"Arquivo de sensores '{file_name}' não encontrado em {json_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Arquivo de sensores '{file_name}' contém JSON inválido.")
        return []
    except Exception as e:
        logger.error(f"Erro ao ler sensores: {e}", exc_info=True)
        return []

def main():
    logger.info("Iniciando Virtual FoT Device...")
    
    # 1. Carregar Configurações (Ambiente e CLI)
    # Em Python, é mais comum usar 'argparse' para CLI
    # Aqui, vamos focar nas variáveis de ambiente por simplicidade
    dev_config = DeviceConfig.load()
    exp_config = ExperimentConfig.load()

    # 2. Configurar Controllers de Log
    # (Usando 'argparse' poderíamos checar por -ps e -ll)
    
    # Exemplo de ativação (poderia ser por CLI)
    activate_persistence = True # CLI.hasParam("-ps", args)
    if activate_persistence:
        msg_controller = MessageLogController.get_instance()
        msg_controller.create_and_update_filename(f"{dev_config.device_id}_ml.csv")
        msg_controller.set_can_save_data(True)
        msg_controller.start()
        
    # (Fazer o mesmo para LatencyLogController e LatencyApiController)
    # api_controller = LatencyApiController(exp_config)
    # api_controller.start()

    # 3. Ler Sensores
    sensors = read_sensors("sensors.json")
    if not sensors:
        logger.critical("Nenhum sensor carregado. Encerrando.")
        return

    # 4. Criar Dispositivo
    device = FoTDevice(dev_config.device_id, sensors, exp_config)

    # 5. Configurar Conexão Inicial
    # O Main.java usa o BrokerUpdateCallback para a conexão inicial
    initial_broker_settings = BrokerSettingsBuilder() \
        .device_id(dev_config.device_id) \
        .set_broker_ip(dev_config.broker_ip) \
        .set_port(str(dev_config.port)) \
        .set_username(dev_config.username) \
        .set_password(dev_config.password) \
        .build()

    logger.info(f"Configurações iniciais do Broker: {initial_broker_settings}")
    
    initial_conn_callback = BrokerUpdateCallback(
        device, 
        exp_config, 
        initial_broker_settings
    )
    
    # Tenta a conexão inicial (is_initial_connection=True)
    timeout = 10.0 # CLI.getTimeout(args)
    initial_conn_callback.start_update_broker(timeout, is_initial_connection=True)

    # 6. Manter o programa principal rodando
    try:
        while True:
            # A lógica principal agora roda nas threads do MQTT e dos sensores
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Recebido sinal de interrupção. Encerrando...")
        device.stop_flow()
        if device.client:
            device.client.loop_stop()
            device.client.disconnect()
        
        if activate_persistence:
            MessageLogController.get_instance().stop()
        # api_controller.stop()
        
        logger.info("Virtual FoT Device encerrado.")

if __name__ == "__main__":
    main()
