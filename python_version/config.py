import os
import uuid
import logging
from dataclasses import dataclass
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DeviceConfig:
    device_id: str
    broker_ip: str
    port: int
    username: str
    password: str
    exp_num: int

    @staticmethod
    def load() -> 'DeviceConfig':
        device_id = os.getenv("DEVICE_ID", str(uuid.uuid4()))
        broker_ip = os.getenv("BROKER_IP", "localhost")
        port = int(os.getenv("PORT", "1883"))
        username = os.getenv("USERNAME", "karaf")
        password = os.getenv("PASSWORD", "karaf")
        exp_num = int(os.getenv("EXP_NUM", "0"))

        logger.info(f"Loaded DeviceConfig: DeviceId={device_id}, BrokerIp={broker_ip}, Port={port}, ExpNum={exp_num}")
        return DeviceConfig(device_id, broker_ip, port, username, password, exp_num)

@dataclass
class ExperimentConfig:
    api_url: str
    buffer_size: int
    exp_num: int
    exp_type: int
    exp_level: int

    @staticmethod
    def load() -> 'ExperimentConfig':
        api_url = os.getenv("API_URL", "http://localhost:8080/api/latency-records/records")
        buffer_size = int(os.getenv("BUFFER_SIZE", "64"))
        exp_num = int(os.getenv("EXP_NUM", "0"))
        exp_type = int(os.getenv("EXP_TYPE", "0"))
        exp_level = int(os.getenv("EXP_LEVEL", "0"))
        
        config = ExperimentConfig(api_url, buffer_size, exp_num, exp_type, exp_level)
        logger.info(f"Loaded {config}")
        return config