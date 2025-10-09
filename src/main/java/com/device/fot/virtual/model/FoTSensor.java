package com.device.fot.virtual.model;

import com.device.fot.virtual.controller.MessageLogController;
import java.util.LinkedList;
import java.util.Random;

import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

import extended.tatu.wrapper.model.Sensor;
import extended.tatu.wrapper.util.TATUWrapper;

/**
 *
 * @author Uellington Damasceno
 */
public class FoTSensor extends Sensor implements Runnable {

    private String deviceId;
    private boolean flow, running;

    private Thread thread;
    private LatencyTrackingMqttClient publisher;

    private String flowThreadName;
    private Random random;

    private int lastValue;

    public FoTSensor(String deviceId, Sensor sensor) {
        this(deviceId,
                sensor.getId(),
                sensor.getType(),
                sensor.getCollectionTime(),
                sensor.getPublishingTime(),
                sensor.getMinValue(),
                sensor.getMaxValue(),
                sensor.getDelta());
    }

    public FoTSensor(String deviceId,
            String sensorName,
            String type,
            int publishingTime,
            int collectionTime, int minValue, int maxValue, int delta) {
        super(sensorName, type, collectionTime, publishingTime, minValue, maxValue, delta);

        this.deviceId = deviceId;
        this.flow = false;
        this.running = false;
        this.random = new Random();
        this.lastValue = (minValue <= 0 && maxValue <= 0) ? 0 : (maxValue - minValue) + minValue;
        this.flowThreadName = this.buildFlowThreadName(deviceId, id);
    }

    public String deviceId() {
        return this.deviceId;
    }

    public void setDeviceId(String deviceId) {
        this.deviceId = deviceId;
    }

    public void setPublisher(LatencyTrackingMqttClient publisher) {
        this.publisher = publisher;
    }

    public boolean isFlow() {
        return this.flow;
    }

    @Override
    public void setPublishingTime(int publishingTime) {
        if (publishingTime >= 1) {
            this.publishingTime = publishingTime;
            return;
        }
        this.stopFlow();
    }

    @Override
    public void setCollectionTime(int collectionTime) {
        if (collectionTime >= 1) {
            this.collectionTime = collectionTime;
            return;
        }
        this.stopFlow();
    }

    public void startFlow() {
        this.startFlow(this.collectionTime, this.publishingTime);
    }

    public void startFlow(int newFlowCollect, int newFlowPublish) {
        if (newFlowCollect >= 1 && newFlowPublish >= 1) {
            this.collectionTime = newFlowCollect;
            this.publishingTime = newFlowPublish;
            if (thread == null || !thread.isAlive()) {
                System.out.println("Sensor type: " + type + " starting flow.");
                this.thread = new Thread(this);
                this.thread.setName(flowThreadName);
                this.thread.start();
            }
            return;
        }
        if (this.running && this.flow) {
            this.stopFlow();
        }
    }

    public void pauseFlow() {
        if (this.thread.isAlive() && this.running) {
            this.running = false;
            this.thread.interrupt();
        }
    }

    public void stopFlow() {
        if (this.thread != null && this.running) {
            this.running = false;
            this.flow = false;
            this.thread.interrupt();
        }
    }

    public boolean isRunnging() {
        return this.running;
    }

    private Data<Integer> getDataFlow() throws InterruptedException {
        var values = new LinkedList<Integer>();
        int tempPublish = this.publishingTime;
        while (tempPublish >= 0) {
            values.add(this.getCurrentValue());
            tempPublish -= this.collectionTime;
            Thread.sleep(this.collectionTime);
        }
        return new Data<>(this.deviceId, this.id, values);
    }

    public Integer getCurrentValue() {
        Integer variation = delta * (random.nextBoolean() ? 1 : -1);
        this.lastValue = Math.min(maxValue, Math.max(minValue, lastValue + variation));
        return lastValue;
    }

    @Override
    public void run() {
        String msg;
        String topic = TATUWrapper.buildTATUResponseTopic(deviceId);
        this.flow = true;
        this.running = true;

        while (thread.isAlive() && this.running && this.flow) {
            try {
                var data = this.getDataFlow();
                msg = TATUWrapper.buildFlowMessageResponse(deviceId, id, publishingTime, collectionTime,
                        data.getValues().toArray());
                this.publisher.publishAndTrack(topic, this.id, msg);
                MessageLogController.getInstance().putData(data);
            } catch (InterruptedException | MqttException ex) {
                this.running = false;
            }
        }
        this.running = false;
    }

    private String buildFlowThreadName(String deviceId, String id) {
        return new StringBuilder("FLOW/")
                .append(deviceId).append("/")
                .append(id).toString();
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("FoTSensor{");
        sb.append("deviceId:").append(deviceId);
        sb.append(", minValue:").append(minValue);
        sb.append(", maxValue:").append(maxValue);
        sb.append(", running:").append(running);
        sb.append('}');
        return sb.toString();
    }
    
}
