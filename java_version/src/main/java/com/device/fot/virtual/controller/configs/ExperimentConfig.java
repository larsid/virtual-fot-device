package com.device.fot.virtual.controller.configs;

import java.util.logging.Logger;

public class ExperimentConfig {

    private String apiUrl;

    private int bufferSize;
    private int expNum;
    private int expType;
    private int expLevel;

    private static final Logger logger = Logger.getLogger(ExperimentConfig.class.getName());

    public ExperimentConfig(String apiUrl, Integer bufferSize, Integer expNum, Integer expType, Integer expLevel) {
        this.apiUrl = apiUrl != null ? apiUrl : "http://localhost:8080/api/latency-records/records";
        this.bufferSize = bufferSize != null ? bufferSize : 64;
        this.expNum = expNum != null ? expNum : 0;
        this.expType = expType != null ? expType : 0;
        this.expLevel = expLevel != null ? expLevel : 0;
    }

    public static ExperimentConfig load() {
        String apiUrl = System.getenv("API_URL");
        String bufferSizeStr = System.getenv("BUFFER_SIZE");
        String expNumStr = System.getenv("EXP_NUM");
        String expTypeStr = System.getenv("EXP_TYPE");
        String expLevelStr = System.getenv("EXP_LEVEL");

        Integer bufferSize = bufferSizeStr != null ? Integer.valueOf(bufferSizeStr) : null;
        Integer expNum = expNumStr != null ? Integer.valueOf(expNumStr) : null;
        Integer expType = expTypeStr != null ? Integer.valueOf(expTypeStr) : null;
        Integer expLevel = expLevelStr != null ? Integer.valueOf(expLevelStr) : null;
        
        return new ExperimentConfig(apiUrl, bufferSize, expNum, expType, expLevel);
    }

    public String getApiUrl() {
        return apiUrl;
    }

    public int getBufferSize() {
        return bufferSize;
    }

    public int getExpNum() {
        return expNum;
    }

    public int getExpType() {
        return expType;
    }

    public int getExpLevel() {
        return expLevel;
    }

    @Override
    public String toString() {
        return "ExperimentConfig {"
                + "apiUrl='" + apiUrl + '\''
                + ", bufferSize=" + bufferSize
                + ", expNum=" + expNum
                + ", expType=" + expType
                + ", expLevel=" + expLevel
                + '}';
    }

}
