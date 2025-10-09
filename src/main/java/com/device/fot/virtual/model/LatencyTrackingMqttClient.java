package com.device.fot.virtual.model;

import com.device.fot.virtual.api.LatencyLoggerApiClient;
import com.device.fot.virtual.controller.LatencyApiController;
import com.device.fot.virtual.controller.configs.ExperimentConfig;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

/**
 *
 * @author Uellington Damasceno
 */
public class LatencyTrackingMqttClient extends MqttClient {

    private static final Logger logger = Logger.getLogger(LatencyTrackingMqttClient.class.getName());

    private final Map<IMqttDeliveryToken, FlightMessageInfo> inFlightMessages;

    private final LatencyApiController latencyApi;

    private final String deviceId, brokerIp;
    private final Integer expNum, expType, expLevel;

    public LatencyTrackingMqttClient(String serverURI, String deviceId, String brokerIp, ExperimentConfig config) throws MqttException {
        super(serverURI, deviceId);

        this.inFlightMessages = new ConcurrentHashMap<>();
        LatencyLoggerApiClient apiClient = new LatencyLoggerApiClient(config.getApiUrl());
        this.latencyApi = new LatencyApiController(apiClient, deviceId, brokerIp, config);

        this.expNum = config.getExpNum();
        this.expType = config.getExpType();
        this.expLevel = config.getExpLevel();
        this.deviceId = deviceId;
        this.brokerIp = brokerIp;
    }

    public IMqttDeliveryToken publishAndTrack(String topic, String sensorId, String message) throws MqttException {
        MqttMessage mqttMessage = new MqttMessage(message.getBytes());
        mqttMessage.setQos(2);

        IMqttDeliveryToken token = this.aClient.publish(topic, mqttMessage, null, null);

        FlightMessageInfo messageInfo = new FlightMessageInfo(sensorId, message);
        this.inFlightMessages.put(token, messageInfo);
        return token;
    }

    public void calculateRTT(IMqttDeliveryToken token) {
        if (!this.inFlightMessages.containsKey(token)) {
            logger.log(Level.INFO, "Não tem mensagem id: {0}", token.getMessageId());
            return;
        }
        FlightMessageInfo messageInfo = this.inFlightMessages.remove(token);

        String messageContent = messageInfo.getMessage();
        String sensorId = messageInfo.getSensorId();
        Long rtt = messageInfo.getElapsedTimeSinceSent();
        LatencyRecord record = LatencyRecord.of(deviceId, sensorId, brokerIp, expNum, expType, expLevel, rtt, messageContent);
        this.latencyApi.putLatencyRecord(record);
    }

}
