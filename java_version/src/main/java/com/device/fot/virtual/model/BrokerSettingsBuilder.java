package com.device.fot.virtual.model;

/**
 *
 * @author Uellington Damasceno
 */
public class BrokerSettingsBuilder {

    private static String deviceId;
    private String brokerIp;
    private String port;
    private String username;
    private String password;

    public static BrokerSettingsBuilder builder() {
        return new BrokerSettingsBuilder();
    }

    public BrokerSettingsBuilder setBrokerIp(String brokerIp) {
        this.brokerIp = brokerIp;
        return this;
    }

    public BrokerSettingsBuilder setPort(String port) {
        this.port = port;
        return this;
    }

    public BrokerSettingsBuilder deviceId(String deviceId) {
        if (BrokerSettingsBuilder.deviceId == null && deviceId != null && !deviceId.isEmpty()) {
            BrokerSettingsBuilder.deviceId = deviceId;
        } 
        return this;
    }

    public BrokerSettingsBuilder setUsername(String username) {
        this.username = username;
        return this;
    }

    public BrokerSettingsBuilder setPassword(String password) {
        this.password = password;
        return this;
    }

    public BrokerSettings build() {
        if (BrokerSettingsBuilder.deviceId == null || BrokerSettingsBuilder.deviceId.isEmpty()) {
            BrokerSettingsBuilder.deviceId = "VIRTUAL_FOT_DEVICE";
        }
        if (this.brokerIp == null || this.brokerIp.isEmpty()) {
            this.brokerIp = "tcp://localhost";
        }else if(!brokerIp.contains("tcp://") && !brokerIp.contains("udp://")){
            this.brokerIp = "tcp://"+brokerIp;
        }
        if (this.port == null || this.port.isEmpty()) {
            this.port = "1883";
        }
        if (this.username == null || this.username.isEmpty()) {
            this.username = "";
        }
        if (this.password == null || this.password.isEmpty()) {
            this.password = "";
        }
        return new BrokerSettings(brokerIp, port, deviceId, username, password);
    }

}
