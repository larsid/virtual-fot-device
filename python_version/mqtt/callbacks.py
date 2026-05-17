import paho.mqtt.client as mqtt
import logging
import json
import threading
import socket
import os
import time  
from typing import TYPE_CHECKING, Optional, Any, Dict

# ... (Imports do Wrapper continuam iguais)
from extended_tatu_wrapper import TATUMessage, ExtendedTATUMethods
from extended_tatu_wrapper.utils import tatu_wrapper, extended_tatu_wrapper

from config import ExperimentConfig
from models.broker_settings import BrokerSettings, BrokerSettingsBuilder
from models.sensor import NULL_FOT_SENSOR

if TYPE_CHECKING:
    from models.device import FoTDevice

logger = logging.getLogger(__name__)

# ... (Classe DefaultFlowCallback continua igual) ...
class DefaultFlowCallback:
    # ... (mesmo código que você já tem) ...
    def __init__(self, device: 'FoTDevice', config: ExperimentConfig):
        self.device = device
        self.config = config
        self.broker_updater: Optional[BrokerUpdateCallback] = None 

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        self._process_message(client, msg)

    def _process_message(self, client: mqtt.Client, msg: mqtt.MQTTMessage):
        try:
            payload = msg.payload.decode('utf-8')
            logger.info(f"[Device: {self.device.id}] Mensagem recebida no tópico '{msg.topic}': {payload}")
            
            tatu_msg = TATUMessage(payload)
            
            if tatu_msg.method == ExtendedTATUMethods.GET:
                self._handle_get(tatu_msg, client)
            
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

    def _handle_get(self, tatu_msg: TATUMessage, client: mqtt.Client):
        sensor = self.device.get_fot_sensor_by_sensor_id(tatu_msg.target) or NULL_FOT_SENSOR
        
        if sensor == NULL_FOT_SENSOR:
            logger.warning(f"Requisição GET para sensor desconhecido: {tatu_msg.target}")
            return
            
        response_payload = tatu_wrapper.build_get_message_response(
            self.device.id,
            sensor.id,
            sensor.get_current_value()
        )
        
        response_topic = tatu_wrapper.build_tatu_response_topic(self.device.id)
        if client.is_connected():
             client.publish(response_topic, response_payload, qos=1)

    def _handle_flow(self, tatu_msg: TATUMessage):
        logger.info(f"Processando FLOW para alvo: {tatu_msg.target}")
        sensor = self.device.get_fot_sensor_by_sensor_id(tatu_msg.target) or NULL_FOT_SENSOR
        
        if sensor == NULL_FOT_SENSOR:
            logger.warning(f"Requisição FLOW para sensor desconhecido: {tatu_msg.target}")
            return

        try:
            flow_data = json.loads(tatu_msg.content)
            
            collect = flow_data.get("collect")
            publish = flow_data.get("publish")

            if collect is None:
                body = flow_data.get("BODY", {})
                if "FLOW" in body and isinstance(body["FLOW"], dict):
                    collect = body["FLOW"].get("collect")
                    publish = body["FLOW"].get("publish")
                else:
                    collect = body.get("collect")
                    publish = body.get("publish")
            
            collect = int(collect) if collect is not None else 0
            publish = int(publish) if publish is not None else 0
            
            logger.info(f"Aplicando FLOW: collect={collect}, publish={publish}")

            if collect <= 0 or publish <= 0:
                sensor.stop_flow()
            else:
                sensor.start_flow(collect, publish)
                
        except Exception as e:
            logger.error(f"Erro ao processar dados do FLOW: {e}", exc_info=True)

    def _handle_set(self, tatu_msg: TATUMessage):
        if tatu_msg.target != "brokerMqtt":
            return
            
        if self.device.is_updating:
            logger.warning("Dispositivo já está atualizando o broker. Ignorando SET.")
            return

        try:
            broker_data = json.loads(tatu_msg.content)
            logger.info(f"Solicitação SET recebida: {broker_data}")
            
            new_broker_settings = BrokerSettingsBuilder() \
                .device_id(self.device.id) \
                .set_broker_ip(broker_data.get("url")) \
                .set_port(str(broker_data.get("port"))) \
                .set_username(broker_data.get("user")) \
                .set_password(broker_data.get("password")) \
                .build()

            self.broker_updater = BrokerUpdateCallback(self.device, self.config, new_broker_settings, self)
            self.broker_updater.start_update_broker(timeout=10.0)
            
        except Exception as e:
            logger.error(f"Falha na atualização via SET: {e}", exc_info=True)
            self.device.is_updating = False

    def on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int):
        if rc != 0:
            logger.error(f"Desconexão inesperada (rc: {rc}).")
        else:
            logger.info("Desconectado.")


class BrokerUpdateCallback:
    
    def __init__(self, device: 'FoTDevice', config: ExperimentConfig, 
                 new_broker_settings: BrokerSettings, flow_handler: DefaultFlowCallback = None):
        self.device = device
        self.config = config
        self.new_broker_settings = new_broker_settings
        self.flow_handler = flow_handler
        self.new_client: Optional[mqtt.Client] = None
        self.timeout_timer: Optional[threading.Timer] = None
        self.ip_address = self._get_ip_address()
        self._is_initial_connection = False
        
        # Variáveis de Exponential Backoff
        self.base_timeout = 10.0
        self.current_timeout = 10.0
        self.max_timeout = 60.0 # Tempo máximo de espera entre tentativas

    def _get_ip_address(self) -> str:
        bind_ip = os.getenv("BIND_IP")
        if bind_ip:
            return bind_ip
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "UNKNOWN_HOST"

    def start_update_broker(self, timeout: float = 10.0, is_initial_connection: bool = False):
        if self.device.is_updating:
            return

        logger.info(f"Iniciando atualização para: {self.new_broker_settings.uri}")
        self.device.is_updating = True
        self._is_initial_connection = is_initial_connection
        
        # Usa o timeout definido na variável de ambiente como base
        self.base_timeout = timeout if timeout > 0 else 10.0
        self.current_timeout = self.base_timeout
        
        try:
            client_id = f"{self.device.id}_CLIENT_UPDATE"
            self.new_client = mqtt.Client(client_id=client_id)
            
            self.new_client.on_connect = self._on_connect_new_broker
            self.new_client.on_message = self._on_generic_message 
            self.new_client.on_disconnect = self._on_disconnect_new_broker

            if self.new_broker_settings.username and self.new_broker_settings.password:
                self.new_client.username_pw_set(self.new_broker_settings.username, self.new_broker_settings.password)
            
            # ==========================================================
            # LOOP DE RESILIÊNCIA: Conexão do Cliente Temporário
            # ==========================================================
            connected = False
            while not connected and self.device.is_updating:
                try:
                    self.new_client.connect(self.new_broker_settings.url, self.new_broker_settings.port)
                    connected = True
                except Exception as e:
                    logger.warning(f"Broker temporário indisponível ({self.new_broker_settings.uri}). Retentando em 5s... Erro: {e}")
                    time.sleep(5)
            # ==========================================================

            if connected:
                self.new_client.loop_start()

        except Exception as e:
            logger.error(f"Falha na conexão update: {e}", exc_info=True)
            self.device.is_updating = False
            if self.new_client:
                self.new_client.loop_stop()

    def _on_connect_new_broker(self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int):
        if rc == 0:
            logger.info(f"Conectado temporariamente a {self.new_broker_settings.uri}")
            try:
                connack_topic = extended_tatu_wrapper.get_connection_topic_response()
                device_topic = tatu_wrapper.build_tatu_topic(self.device.id)
                
                client.subscribe([(connack_topic, 1), (device_topic, 1)])
                logger.info(f"Inscrito em {connack_topic} e {device_topic}")
                time.sleep(0.5) 
                
                # Inicia o ciclo de disparo do CONNECT
                self._send_connect_and_schedule_timeout()
                
            except Exception as e:
                logger.error(f"Erro no handshake: {e}", exc_info=True)
                self._cleanup_new_client()
        else:
            logger.error(f"Falha na conexão temporária (rc: {rc})")

    # ==========================================================
    # LÓGICA DO BACKOFF E RETENTATIVA DO HANDSHAKE
    # ==========================================================
    def _send_connect_and_schedule_timeout(self):
        try:
            connect_topic = extended_tatu_wrapper.get_connection_topic()
            connect_msg = extended_tatu_wrapper.build_connect_message(self.device, self.ip_address, self.current_timeout)
            
            self.new_client.publish(connect_topic, connect_msg, qos=1)
            logger.info(f"Mensagem CONNECT enviada. Aguardando CONNACK por {self.current_timeout}s...")
            
            if self.timeout_timer:
                self.timeout_timer.cancel()
            
            self.timeout_timer = threading.Timer(self.current_timeout, self._on_timeout)
            self.timeout_timer.start()
            
        except Exception as e:
            logger.error(f"Erro ao enviar CONNECT: {e}")

    def _on_timeout(self):
        logger.warning(f"Timeout! Sem resposta do Gateway. Reenviando CONNECT...")
        
        # Exponential backoff: Dobra o tempo de espera até o limite máximo
        self.current_timeout = min(self.current_timeout * 2, self.max_timeout)
        
        # Dispara de novo
        self._send_connect_and_schedule_timeout()
    # ==========================================================

    def _on_generic_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        connack_topic = extended_tatu_wrapper.get_connection_topic_response()
        
        if topic == connack_topic:
            self._handle_connack(client, msg)
        else:
            if self.flow_handler:
                self.flow_handler._process_message(client, msg)

    def _handle_connack(self, client: mqtt.Client, msg: mqtt.MQTTMessage):
        payload = msg.payload.decode('utf-8')
        tatu_msg = TATUMessage(payload)
        
        if tatu_msg.method != ExtendedTATUMethods.CONNACK:
            return

        try:
            connack_data = json.loads(tatu_msg.content)
            
            
            # Pega o nome do dispositivo que o Gateway está aprovando
            target_device = connack_data.get("BODY", {}).get("NEW_NAME", "")
            
            # Se a aprovação não for para ESTE dispositivo, ignora a mensagem silenciosamente
            if target_device != self.device.id:
                return
            
            
            # Se chegou aqui, é porque o CONNACK é realmente para ele!
            if self.timeout_timer:
                self.timeout_timer.cancel()
                
            logger.info(f"Recebido CONNACK destinado a mim: {payload}")
            can_connect = connack_data.get("BODY", {}).get("CAN_CONNECT", False)
            
            if can_connect:
                logger.info("Conexão APROVADA. Iniciando transição de cliente...")
                threading.Thread(target=self._perform_switch).start()
            else:
                logger.warning("Conexão NEGADA.")
                self.device.is_updating = False
                self._cleanup_new_client()
        
        except json.JSONDecodeError:
            logger.error("JSON CONNACK inválido.")
            self.device.is_updating = False
            self._cleanup_new_client()

    def _perform_switch(self):
        try:
            self.device.update_broker_settings(self.new_broker_settings)
            
            logger.info("Cliente principal conectado. Mantendo cliente temporário por 5s para overlap...")
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Erro na transição: {e}")
        finally:
            logger.info("Transição concluída. Encerrando cliente temporário.")
            self._cleanup_new_client()

    def _on_disconnect_new_broker(self, client: mqtt.Client, userdata: Any, rc: int):
        logger.info(f"Cliente temporário desconectado (rc: {rc})")

    def _cleanup_new_client(self):
        if self.timeout_timer:
            self.timeout_timer.cancel()
            
        if self.new_client:
            try:
                self.new_client.loop_stop()
                self.new_client.disconnect()
            except Exception as e:
                logger.error(f"Erro limpeza cliente update: {e}")