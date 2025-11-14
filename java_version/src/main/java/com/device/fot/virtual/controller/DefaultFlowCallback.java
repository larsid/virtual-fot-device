package com.device.fot.virtual.controller;

import com.device.fot.virtual.controller.configs.ExperimentConfig;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.json.JSONObject;

import com.device.fot.virtual.model.BrokerSettings;
import com.device.fot.virtual.model.BrokerSettingsBuilder;
import com.device.fot.virtual.model.FoTDevice;
import com.device.fot.virtual.model.FoTSensor;
import com.device.fot.virtual.model.NullFoTSensor;

import extended.tatu.wrapper.model.TATUMessage;
import extended.tatu.wrapper.util.TATUWrapper;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author Uelligton Damasceno
 */
public class DefaultFlowCallback implements MqttCallback {

    private FoTDevice device;
    private BrokerUpdateCallback brokerUpdateController;
    private static final Logger logger = Logger.getLogger(DefaultFlowCallback.class.getName());

    public DefaultFlowCallback(FoTDevice device, ExperimentConfig config) {
        this.device = device;
        this.brokerUpdateController = new BrokerUpdateCallback(device, config);
    }

    @Override
    public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
        String messagePayload = new String(mqttMessage.getPayload());
        TATUMessage tatuMessage = new TATUMessage(messagePayload);
        MqttMessage mqttResponse = new MqttMessage();
        FoTSensor sensor;

        logger.log(Level.INFO, "Message arrived on topic ''{0}'': {1}", new Object[]{topic, messagePayload});
        logger.log(Level.INFO, "Parsed TATU Message for device ''{0}'' on topic ''{1}'': Method={2}, Target=''{3}'', Content=''{4}''",
                new Object[]{device.getId(), topic, tatuMessage.getMethod(), tatuMessage.getTarget(), tatuMessage.getMessageContent()});

        switch (tatuMessage.getMethod()) {
            case FLOW:
                logger.log(Level.INFO, "Processing FLOW request for target: {0}", tatuMessage.getTarget());
                sensor = (FoTSensor) device.getSensorBySensorId(tatuMessage.getTarget())
                        .orElse(NullFoTSensor.getInstance());
                if (sensor instanceof NullFoTSensor) {
                    logger.log(Level.WARNING, "FLOW request for unknown sensor: {0}", tatuMessage.getTarget());
                    break;
                }
                JSONObject flow = new JSONObject(tatuMessage.getMessageContent());
                sensor.startFlow(flow.getInt("collect"), flow.getInt("publish"));
                break;
            case GET:
                sensor = (FoTSensor) device.getSensorBySensorId(tatuMessage.getTarget())
                        .orElse(NullFoTSensor.getInstance());
                String jsonResponse = TATUWrapper.buildGetMessageResponse(device.getId(),
                        sensor.getId(),
                        sensor.getCurrentValue());

                mqttResponse.setPayload(jsonResponse.getBytes());
                String publishTopic = TATUWrapper.buildTATUResponseTopic(device.getId());
                this.device.publish(publishTopic, mqttResponse);
                break;
            case SET:
                logger.log(Level.INFO, "Processing SET request for target: {0}", tatuMessage.getTarget());
                if (this.device.isUpdating()) {
                    logger.log(Level.WARNING, "Device {0} is currently updating its broker. Ignoring SET brokerMqtt request.", device.getId());
                    break;
                }
                var newMessage = tatuMessage.getMessageContent();
                logger.log(Level.INFO, "SET brokerMqtt payload: {0}", newMessage);
                var newBrokerSettingsJson = new JSONObject(newMessage);
                var id = newBrokerSettingsJson.getString("id");
                var ip = newBrokerSettingsJson.getString("url");
                var port = newBrokerSettingsJson.getString("port");
                logger.log(Level.WARNING, "Change to gateway id {0} ip:port: {1}:{2}", new Object[]{id, ip, port});
                BrokerSettings newBrokerSettings = BrokerSettingsBuilder.builder()
                        .deviceId(id)
                        .setBrokerIp(ip)
                        .setPort(port)
                        .setUsername(newBrokerSettingsJson.getString("user"))
                        .setPassword(newBrokerSettingsJson.getString("password"))
                        .build();

                logger.log(Level.WARNING, "Change to gateway id {0} ip:port: {1}:{2}", new Object[]{id, id, port});

                this.brokerUpdateController.startUpdateBroker(newBrokerSettings, 10.000, false);

                break;
            case EVT:
                logger.log(Level.INFO, "Received EVT request (currently not supported) for target: {0}", tatuMessage.getTarget());
                break;
            case POST:
                logger.log(Level.INFO, "Received POST request for target: {0}. No specific action implemented in this callback.", tatuMessage.getTarget());
                break;
            case INVALID:
                System.out.println("Invalid message!");
                break;
            default:
                logger.log(Level.SEVERE, "Unsupported TATU method encountered: {0} on topic {1}", new Object[]{tatuMessage.getMethod().name(), topic});
                throw new AssertionError(tatuMessage.getMethod().name());
        }

    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken imdt) {
        this.device.calculateLatency(imdt);
    }

    @Override
    public void connectionLost(Throwable cause) {
        logger.log(Level.SEVERE, "MQTT connection lost for device " + device.getId() + ". Cause: " + cause.getMessage(), cause);
    }
}
