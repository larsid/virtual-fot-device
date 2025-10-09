package com.device.fot.virtual.model;

/**
 *
 * @author Uellington Damasceno
 */
public class FlightMessageInfo {
    private final String sensorId;
    private final Long timestamp;
    private final String message;

    public FlightMessageInfo(String sensorId, String message){
        this(sensorId, System.nanoTime(), message);
    }
    
    public FlightMessageInfo(String sensorId, Long timestamp, String message) {
        this.sensorId = sensorId;
        this.timestamp = timestamp;
        this.message = message;
    }

    public String getSensorId() {
        return sensorId;
    }

    public Long getTimestamp() {
        return timestamp;
    }

    public String getMessage() {
        return message;
    }

    public long getElapsedTimeSinceSent() {
        return System.nanoTime() - this.timestamp;
    }
}
