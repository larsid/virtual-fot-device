package com.device.fot.virtual.model;

/**
 *
 * @author Uellington Damasceno
 */
public class LatencyRecord {

    private String deviceID;

    private Integer experiment;
    private int type;
    private int level;
    private Long latency;
    private String sensorId;
    private String brokerIp;
    private String message;

    public LatencyRecord(String deviceID,
            String sensorId,
            String brokerIp,
            Integer experiment,
            Integer type,
            Integer level,
            Long latency,
            String message) {

        this.deviceID = deviceID;
        this.sensorId = sensorId;
        this.brokerIp = brokerIp;
        this.experiment = experiment;
        this.type = type;
        this.level = level;
        this.latency = latency;
        this.message = message;
    }

    public static LatencyRecord of(String deviceID,
            String sensorId,
            String brokerIp,
            Integer experiment,
            Integer type,
            Integer level,
            Long latency,
            String message) {
        return new LatencyRecord(deviceID, sensorId, brokerIp, experiment, type, level, latency, message);
    }

    public String getDeviceID() {
        return deviceID;
    }

    public void setDeviceID(String deviceID) {
        this.deviceID = deviceID;
    }

    public Integer getType() {
        return type;
    }

    public void setType(Integer type) {
        this.type = type;
    }

    public Integer getLevel() {
        return level;
    }

    public void setLevel(Integer level) {
        this.level = level;
    }

    public Integer getExperiment() {
        return experiment;
    }

    public void setExperiment(Integer experiment) {
        this.experiment = experiment;
    }

    public Long getLatency() {
        return latency;
    }

    public void setLatency(Long latency) {
        this.latency = latency;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getSensorId() {
        return sensorId;
    }

    public void setSensorId(String sensorId) {
        this.sensorId = sensorId;
    }

    public String getBrokerIp() {
        return brokerIp;
    }

    public void setBrokerIp(String brokerIp) {
        this.brokerIp = brokerIp;
    }

}
