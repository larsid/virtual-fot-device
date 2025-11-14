package com.device.fot.virtual.controller;

import com.device.fot.virtual.controller.configs.ExperimentConfig;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.json.JSONObject;

import com.device.fot.virtual.model.BrokerSettings;
import com.device.fot.virtual.model.FoTDevice;

import extended.tatu.wrapper.enums.ExtendedTATUMethods;
import extended.tatu.wrapper.model.TATUMessage;
import extended.tatu.wrapper.util.ExtendedTATUWrapper;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author Uellington Damasceno
 */
public class BrokerUpdateCallback implements MqttCallback, Runnable {

    private static final Logger logger = Logger.getLogger(BrokerUpdateCallback.class.getName());

    private FoTDevice device;
    private BrokerSettings brokerSettings;
    private Thread timeoutCounter;
    private String ip;
    private ExperimentConfig config;

    public BrokerUpdateCallback(FoTDevice device, ExperimentConfig config) {
        this.device = device;
        this.ip = this.getIpAddress();
        this.config = config;
    }

    public void startUpdateBroker(BrokerSettings brokerSettings, double timeout, boolean retryConnect) {
        if (this.device.isUpdating()) {
            logger.log(Level.INFO, "Device {0} is already in the process of updating the broker. Ignoring new request.", device.getId());
            return;
        }
        logger.log(Level.INFO, "Device {0} starting broker update process for: {1}", new Object[]{device.getId(), brokerSettings.getUrl()});

        this.device.setIsUpdating(true);
        MqttConnectOptions newOptions = brokerSettings.getConnectionOptions();
        String connectionTopic = ExtendedTATUWrapper.getConnectionTopic();
        String message = ExtendedTATUWrapper.buildConnectMessage(device, ip, timeout);
        this.timeoutCounter = new Thread(this);
        this.timeoutCounter.setName("BROKER/UPDATE/TIMEOUT");

        try {
            MqttClient newClient = brokerSettings.getClient(config);

            newClient.setCallback(this);

            this.tryConnect(newClient, newOptions, retryConnect);

            newClient.subscribe(ExtendedTATUWrapper.getConnectionTopicResponse());
            newClient.publish(connectionTopic, new MqttMessage(message.getBytes()));
            this.brokerSettings = brokerSettings;
            this.timeoutCounter.start();

        } catch (MqttException ex) {
            brokerSettings.disconnectClient();
            device.setIsUpdating(false);
        }
    }

    @Override
    public void connectionLost(Throwable cause) {
        logger.log(Level.SEVERE, "MQTT connection lost for device " + device.getId() + " with broker " + (brokerSettings != null ? brokerSettings.getUri() : "UNKNOWN_BROKER") + ". Cause: " + cause.getMessage(), cause);
    }

    @Override
    public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
        String messagePayload = new String(mqttMessage.getPayload());
        logger.log(Level.INFO, "Message arrived on topic ''{0}'': {1}", new Object[]{topic, messagePayload}); // FINER for raw message

        TATUMessage tatuMessage = new TATUMessage(messagePayload);
        if (!tatuMessage.isResponse() || !tatuMessage.getMethod().equals(ExtendedTATUMethods.CONNACK)) {
            logger.log(Level.WARNING, "Parsed TATUMessage from topic ''{0}'': Method={1}, Target={2}", new Object[]{topic, tatuMessage.getMethod(), tatuMessage.getTarget()});
            return;
        }
        this.timeoutCounter.interrupt();
        var json = new JSONObject(tatuMessage.getMessageContent());
        boolean canConnect = json.getJSONObject("BODY").getBoolean("CAN_CONNECT");

        logger.log(Level.INFO, "CONNACK received for device {0}: CAN_CONNECT={1}. New broker: {2}", new Object[]{device.getId(), canConnect, brokerSettings.getUri()});

        if (canConnect) {
            this.device.updateBrokerSettings(brokerSettings);
            this.brokerSettings.getClient(config).unsubscribe(ExtendedTATUWrapper.getConnectionTopicResponse());
            logger.log(Level.INFO, "Device {0} successfully updated to new broker: {1}. Unsubscribed from connection response topic.", new Object[]{device.getId(), brokerSettings.getUri()});
            device.setIsUpdating(false);
        } else {
            this.brokerSettings.disconnectClient();
            logger.log(Level.WARNING, "Device {0} connection to new broker {1} denied by CONNACK. Disconnecting new client.", new Object[]{device.getId(), brokerSettings.getUri()});
        }
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
    }

    @Override
    public void run() {
        try {
            Thread.sleep(10000L);
            if (this.device.isUpdating()) {
                logger.log(Level.WARNING, "Broker update for device {0} timed out. Disconnecting client for {1}.", new Object[]{device.getId(), brokerSettings.getUri()});
                this.device.setIsUpdating(false);
                this.brokerSettings.disconnectClient();
            }
        } catch (InterruptedException ex) {
            logger.log(Level.INFO, "Broker update timeout thread for device {0} was interrupted, likely due to successful CONNACK or shutdown.", device.getId());
        }
    }

    public void tryConnect(MqttClient client, MqttConnectOptions options, boolean retryConnect) {
        boolean connected = false;
        do {
            try {
                logger.log(Level.INFO, "Attempting to connect to broker: {0} for device: {1}", new Object[]{client.getServerURI(), device.getId()});
                client.connect(options);
                logger.log(Level.INFO, "Successfully connected to broker: {0} for device: {1}", new Object[]{client.getServerURI(), device.getId()});
                connected = true;
            } catch (MqttException e) {
                logger.log(Level.WARNING, "Failed to connect to broker: " + client.getServerURI() + " on attempt. Retrying: " + retryConnect, e);
                if (!retryConnect) {
                    return;
                }
                try {
                    Thread.sleep(1000L);
                } catch (InterruptedException ex) {
                }
            }
        } while (!connected && retryConnect);
    }

    public final String getIpAddress() {
        try {
            InetAddress localhost = InetAddress.getLocalHost();
            return localhost.getHostAddress();
        } catch (UnknownHostException e) {
            return "UNKNOWN_HOST";
        }
    }
}
