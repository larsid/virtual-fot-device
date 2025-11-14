package com.device.fot.virtual.model;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

public class Data<T> {

    private final long timestamp;
    private final String deviceId;
    private final String sensorId;
    private final List<T> values;

    public Data(String deviceId, String sensorId, List<T> values) {
        this(deviceId, sensorId, values, Instant.now().toEpochMilli());
    }

    public Data(String deviceId, String sensorId, List<T> values, long timestamp) {
        this.deviceId = deviceId;
        this.sensorId = sensorId;
        this.values = values;
        this.timestamp = timestamp;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public String getDeviceId() {
        return deviceId;
    }

    public String getSensorId() {
        return sensorId;
    }

    public List<T> getValues() {
        return values;
    }

    private String valuesToString() {
        return this.values
                .stream()
                .map(T::toString)
                .collect(Collectors.joining(","));
    }

    @Override
    public String toString() {
        return new StringBuilder()
                .append(timestamp).append(",")
                .append(deviceId).append(",")
                .append(sensorId).append(",")
                .append(valuesToString())
                .toString();

    }
}
