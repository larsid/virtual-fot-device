package com.device.fot.virtual.controller;

import com.device.fot.virtual.api.LatencyLoggerApiClient;
import com.device.fot.virtual.controller.configs.ExperimentConfig;
import com.device.fot.virtual.model.LatencyRecord;
import java.io.IOException;
import java.util.ArrayList;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author Uellington Damasceno
 */
public class LatencyApiController implements Runnable {

    private static final Logger logger = Logger.getLogger(LatencyApiController.class.getName());
    private final LatencyLoggerApiClient apiClient;
    private final LinkedBlockingQueue<LatencyRecord> buffer;
    private boolean running;

    protected Thread thread;
    private final Integer bufferSize;

    public LatencyApiController(LatencyLoggerApiClient apiClient,
            String deviceId,
            String brokerIp,
            ExperimentConfig config) {

        this.apiClient = apiClient;
        this.buffer = new LinkedBlockingQueue<>();
        this.bufferSize = config.getBufferSize();

    }

    public void start() {
        if (this.thread == null || !running) {
            this.thread = new Thread(this);
            this.thread.setDaemon(true);
            this.thread.setName("LATENCY_LOGGER_API_WRITER");
            this.thread.start();
        }
    }

    public void stop() {
        running = false;
    }
    
    public void putLatencyRecord(LatencyRecord record){
        this.buffer.add(record);
    }
    
    @Override
    public void run() {
        running = true;
        var latencyLines = new ArrayList<LatencyRecord>(bufferSize);
        while (running) {
            try {
                if (buffer.isEmpty()) {
                    continue;
                }
                latencyLines.add(buffer.take());

                if (latencyLines.size() >= bufferSize) {
                    apiClient.postAllLatencies(latencyLines);
                    latencyLines.clear();
                }
            } catch (InterruptedException | IOException ex) {
                logger.log(Level.SEVERE, null, ex);
                this.running = false;
            }
        }
    }

}
