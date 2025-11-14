package com.device.fot.virtual.controller.configs;

import java.util.UUID;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author Uellington Damasceno
 */
public class DeviceConfig {

    private String deviceId;
    private String brokerIp;
    private String port;
    private String username;
    private String password;

    private String expNum;
    
     private static final Logger logger = Logger.getLogger(DeviceConfig.class.getName());


    public DeviceConfig(String deviceId, String brokerIp, String port, String username, String password, String expNum) {
        this.deviceId = deviceId == null ? UUID.randomUUID().toString() : deviceId;
        this.brokerIp = brokerIp == null ? "localhost": brokerIp;
        this.port = port == null ? "1883" : port;
        this.username = username == null ? "karaf" : username;
        this.password = password == null ? "karaf" : password;
        this.expNum = expNum == null ? "0" : expNum;
    }


    public static DeviceConfig load() {
        String deviceId = System.getenv("DEVICE_ID");
        String brokerIp = System.getenv("BROKER_IP");
        String port = System.getenv("PORT");
        String username = System.getenv("USERNAME");
        String password = System.getenv("PASSWORD");
        String expNum = System.getenv("EXP_NUM");

        logger.log(Level.INFO, "Loaded configuration: DeviceId = {0}, BrokerIp = {1}, Port = {2}, Username = {3}, Password = {4}, ExpNum = {5}",
                new Object[]{deviceId != null ? deviceId : "Default", brokerIp != null ? brokerIp : "Default", port != null ? port : "Default",
                    username != null ? username : "Default", password != null ? password : "Default", expNum != null ? expNum : "Default"});

        return new DeviceConfig(deviceId, brokerIp, port, username, password, expNum);
    }

    public String getDeviceId() {
        return deviceId;
    }

    public String getBrokerIp() {
        return brokerIp;
    }

    public String getPort() {
        return port;
    }

    public String getUsername() {
        return username;
    }

    public String getPassword() {
        return password;
    }

    public String getExpNum() {
        return expNum;
    }

}
