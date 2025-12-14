import sys
import json
import logging
import time
from pathlib import Path
from typing import List
from extended_tatu_wrapper import Sensor 
from extended_tatu_wrapper.utils import sensor_wrapper 
from models.device import FoTDevice
from models.broker_settings import BrokerSettingsBuilder
from config import DeviceConfig, ExperimentConfig
# --- MUDANÇA 1: Importar DefaultFlowCallback ---
from mqtt.callbacks import BrokerUpdateCallback, DefaultFlowCallback
from controllers.persistense import MessageLogController
from controllers.api_controller import LatencyApiController

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_sensors_from_file(file_name: str) -> List[Sensor]:
    try:
        json_path = Path(__file__).parent / file_name
        with json_path.open('r', encoding='utf-8') as f:
            sensors_data = json.load(f)
        return sensor_wrapper.get_all_sensors(sensors_data)
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
    
    dev_config = DeviceConfig.load()
    exp_config = ExperimentConfig.load()

    activate_persistence = True 
    if activate_persistence:
        msg_controller = MessageLogController.get_instance()
        msg_controller.create_and_update_filename(f"{dev_config.device_id}_ml.csv")
        msg_controller.set_can_save_data(True)
        msg_controller.start()
        
    api_controller = LatencyApiController(exp_config)
    api_controller.start()

    sensors = read_sensors_from_file("sensors.json")
    if not sensors:
        logger.critical("Nenhum sensor carregado. Encerrando.")
        return

    device = FoTDevice(dev_config.device_id, sensors, exp_config)

    initial_broker_settings = BrokerSettingsBuilder() \
        .device_id(dev_config.device_id) \
        .set_broker_ip(dev_config.broker_ip) \
        .set_port(str(dev_config.port)) \
        .set_username(dev_config.username) \
        .set_password(dev_config.password) \
        .build()

    logger.info(f"Configurações iniciais do Broker: {initial_broker_settings}")
    
    # --- MUDANÇA 2: Criar o handler de fluxo ---
    # Este objeto sabe como processar mensagens GET/FLOW/SET
    flow_handler = DefaultFlowCallback(device, exp_config)

    initial_conn_callback = BrokerUpdateCallback(
        device, 
        exp_config, 
        initial_broker_settings,
        flow_handler=flow_handler  # --- MUDANÇA 3: Passar o handler aqui! ---
    )
    
    initial_conn_callback.start_update_broker(timeout=dev_config.timeout, is_initial_connection=True)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Recebido sinal de interrupção. Encerrando...")
        device.stop_flow()
        if device.client:
            device.client.loop_stop()
            device.client.disconnect()
        
        if activate_persistence:
            MessageLogController.get_instance().stop()
        api_controller.stop()
        
        logger.info("Virtual FoT Device encerrado.")

if __name__ == "__main__":
    main()