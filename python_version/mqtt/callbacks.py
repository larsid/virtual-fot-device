import paho.mqtt.client as mqtt
import logging
import json
import threading
import socket
from typing import TYPE_CHECKING, Optional, Any, Dict

# Imports do Wrapper Oficial
from extended_tatu_wrapper import TATUMessage, ExtendedTATUMethods
from extended_tatu_wrapper.utils import tatu_wrapper, extended_tatu_wrapper

from config import ExperimentConfig
from models.broker_settings import BrokerSettings, BrokerSettingsBuilder
from models.sensor import NULL_FOT_SENSOR

if TYPE_CHECKING:
    from models.device import FoTDevice

logger = logging.getLogger(__name__)

class DefaultFlowCallback:
    
    def __init__(self, device: 'FoTDevice', config: ExperimentConfig):
        self.device = device
        self.config = config
        self.broker_updater: Optional[BrokerUpdateCallback] = None

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        try:
            payload = msg.payload.decode('utf-8')
            logger.info(f"[Device: {self.device.id}] Mensagem recebida no tópico '{msg.topic}': {payload}")
            
            # Usa o parser TATUMessage oficial
            tatu_msg = TATUMessage(payload)
            
            if tatu_msg.method == ExtendedTATUMethods.GET:
                self._handle_get(tatu_msg)
            
            elif tatu_msg.method == ExtendedTATUMethods.FLOW:
                self._handle_flow(tatu_msg)
            
            elif tatu_msg.method == ExtendedTATUMethods.SET:
                self._handle_set(tatu_msg)
            
            elif tatu_msg.method == ExtendedTATUMethods.INVALID:
                logger.warning(f"Mensagem TATU inválida recebida: {payload}")
            
            else:
                logger.info(f"Método TATU {tatu_msg.method.name} recebido, mas não tratado.")

        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {e}", exc_info=True)

    def _handle_get(self, tatu_msg: TATUMessage):
        # O parser oficial identifica o 'target' (nome do sensor)
        sensor = self.device.get_fot_sensor_by_sensor_id(tatu_msg.target) or NULL_FOT_SENSOR
        
        if sensor == NULL_FOT_SENSOR:
            logger.warning(f"Requisição GET para sensor desconhecido: {tatu_msg.target}")
            return
            
        # Usa o wrapper oficial para construir a resposta
        response_payload = tatu_wrapper.build_get_message_response(
            self.device.id,
            sensor.id,
            sensor.get_current_value()
        )
        
        response_topic = tatu_wrapper.build_tatu_response_topic(self.device.id)
        if self.device.client:
            self.device.client.publish(response_topic, response_payload, qos=1)

    def _handle_flow(self, tatu_msg: TATUMessage):
        sensor = self.device.get_fot_sensor_by_sensor_id(tatu_msg.target) or NULL_FOT_SENSOR
        
        if sensor == NULL_FOT_SENSOR:
            logger.warning(f"Requisição FLOW para sensor desconhecido: {tatu_msg.target}")
            return

        try:
            # O parser oficial coloca o JSON no 'content'
            flow_data = json.loads(tatu_msg.content)
            collect = flow_data.get("collect", 0)
            publish = flow_data.get("publish", 0)
            
            if collect <= 0 or publish <= 0:
                sensor.stop_flow()
            else:
                sensor.start_flow(collect, publish)
                
        except json.JSONDecodeError:
            logger.error(f"Payload JSON inválido para FLOW: {tatu_msg.content}")

    def _handle_set(self, tatu_msg: TATUMessage):
        # O parser oficial identifica 'brokerMqtt' como o 'target'
        if tatu_msg.target != "brokerMqtt":
            logger.warning(f"Requisição SET não suportada para o alvo: {tatu_msg.target}")
            return
            
        if self.device.is_updating:
            logger.warning(f"Dispositivo {self.device.id} já está atualizando o broker. Ignorando SET.")
            return

        try:
            # O parser oficial coloca o JSON no 'content'
            broker_data = json.loads(tatu_msg.content)
            logger.info(f"Recebida solicitação SET para novo broker: {broker_data}")
            
            new_broker_settings = BrokerSettingsBuilder() \
                .device_id(self.device.id) \
                .set_broker_ip(broker_data.get("url")) \
                .set_port(str(broker_data.get("port"))) \
                .set_username(broker_data.get("user")) \
                .set_password(broker_data.get("password")) \
                .build()

            self.broker_updater = BrokerUpdateCallback(self.device, self.config, new_broker_settings)
            self.broker_updater.start_update_broker(timeout=10.0)
            
        except json.JSONDecodeError:
            logger.error(f"Payload JSON inválido para SET brokerMqtt: {tatu_msg.content}")
        except Exception as e:
            logger.error(f"Falha ao iniciar a atualização do broker: {e}", exc_info=True)
            self.device.is_updating = False

    def on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int):
        if rc != 0:
            logger.error(f"Dispositivo {self.device.id} desconectado inesperadamente (rc: {rc}).")
        else:
            logger.info(f"Dispositivo {self.device.id} desconectado.")


class BrokerUpdateCallback:
    
    def __init__(self, device: 'FoTDevice', config: ExperimentConfig, new_broker_settings: BrokerSettings):
        self.device = device
        self.config = config
        self.new_broker_settings = new_broker_settings
        self.new_client: Optional[mqtt.Client] = None
        self.timeout_timer: Optional[threading.Timer] = None
        self.ip_address = self._get_ip_address()
        self._is_initial_connection = False

    def _get_ip_address(self) -> str:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "UNKNOWN_HOST"

    def start_update_broker(self, timeout: float = 10.0, is_initial_connection: bool = False):
        if self.device.is_updating:
            logger.warning("Processo de atualização já em andamento.")
            return

        logger.info(f"Dispositivo {self.device.id} iniciando processo de atualização para: {self.new_broker_settings.uri}")
        self.device.is_updating = True
        self._is_initial_connection = is_initial_connection
        
        try:
            client_id = f"{self.device.id}_CLIENT_UPDATE"
            self.new_client = mqtt.Client(client_id=client_id)
            
            self.new_client.on_connect = self._on_connect_new_broker
            self.new_client.on_message = self._on_message_connack
            self.new_client.on_disconnect = self._on_disconnect_new_broker

            if self.new_broker_settings.username and self.new_broker_settings.password:
                self.new_client.username_pw_set(self.new_broker_settings.username, self.new_broker_settings.password)
            
            self.new_client.connect(self.new_broker_settings.url, self.new_broker_settings.port)
            self.new_client.loop_start()

            self.timeout_timer = threading.Timer(timeout, self._on_timeout)
            self.timeout_timer.start()

        except Exception as e:
            logger.error(f"Falha ao conectar ao novo broker: {e}", exc_info=True)
            self.device.is_updating = False
            if self.new_client:
                self.new_client.loop_stop()

    def _on_connect_new_broker(self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int):
        if rc == 0:
            logger.info(f"Conexão temporária estabelecida com {self.new_broker_settings.uri}")
            try:
                # Usa o wrapper oficial
                connack_topic = extended_tatu_wrapper.get_connection_topic_response()
                client.subscribe(connack_topic)
                logger.info(f"Inscrito em {connack_topic}")
                
                # Usa o wrapper oficial
                connect_topic = extended_tatu_wrapper.get_connection_topic()
                connect_msg = extended_tatu_wrapper.build_connect_message(self.device, self.ip_address, 10.0)
                client.publish(connect_topic, connect_msg, qos=1)
                logger.info(f"Publicada mensagem CONNECT em {connect_topic}")
                
            except Exception as e:
                logger.error(f"Falha ao publicar/inscrever após conexão: {e}", exc_info=True)
                self._cleanup_new_client()
        else:
            logger.error(f"Falha na conexão temporária com o novo broker (rc: {rc})")
            self.device.is_updating = False
            if not self._is_initial_connection:
                 self._cleanup_new_client() 


    def _on_message_connack(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        if self.timeout_timer:
            self.timeout_timer.cancel()
        
        payload = msg.payload.decode('utf-8')
        logger.info(f"Recebido CONNACK: {payload}")
        
        # Usa o parser TATUMessage oficial
        tatu_msg = TATUMessage(payload)
        
        if tatu_msg.method != ExtendedTATUMethods.CONNACK:
            logger.warning("Recebida mensagem que não é CONNACK. Ignorando.")
            return

        try:
            # O parser oficial coloca o JSON no 'content'
            connack_data = json.loads(tatu_msg.content)
            can_connect = connack_data.get("BODY", {}).get("CAN_CONNECT", False)
            
            if can_connect:
                logger.info(f"CONNACK recebido: Conexão APROVADA para {self.new_broker_settings.uri}")
                self.device.update_broker_settings(self.new_broker_settings)
            else:
                logger.warning(f"CONNACK recebido: Conexão NEGADA para {self.new_broker_settings.uri}")
                self.device.is_updating = False
        
        except json.JSONDecodeError:
            logger.error(f"Payload JSON inválido para CONNACK: {tatu_msg.content}")
            self.device.is_updating = False
        finally:
            self._cleanup_new_client()

    def _on_timeout(self):
        logger.warning(f"Timeout ao esperar por CONNACK de {self.new_broker_settings.uri}")
        self.device.is_updating = False
        self._cleanup_new_client()
        
        if self._is_initial_connection:
            logger.critical("Falha ao obter CONNACK na conexão inicial. Encerrando.")
            # Aqui poderíamos sair do programa
            # raise SystemExit("Falha na conexão inicial (timeout CONNACK)")

    def _on_disconnect_new_broker(self, client: mqtt.Client, userdata: Any, rc: int):
        logger.info(f"Cliente de atualização desconectado (rc: {rc})")

    def _cleanup_new_client(self):
        if self.timeout_timer:
            self.timeout_timer.cancel()
            
        if self.new_client:
            try:
                self.new_client.loop_stop()
                self.new_client.disconnect()
            except Exception as e:
                logger.error(f"Erro ao limpar cliente de atualização: {e}")