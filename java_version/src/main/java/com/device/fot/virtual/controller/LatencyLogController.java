package com.device.fot.virtual.controller;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

public class LatencyLogController extends FilePersistenceController<Long> {

    private static final Logger logger = Logger.getLogger(LatencyLogController.class.getName());
    private static final LatencyLogController latencyLogController = new LatencyLogController();

    private static final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("HH:mm:ss.SSS");
    private final Map<Integer, String> messages;

    private LatencyLogController() {
        super("latency_log.csv");
        this.messages = new HashMap<>();
    }

    public synchronized static LatencyLogController getInstance() {
        return latencyLogController;
    }

    public void putNewMessage(int id, String message) {
        this.messages.put(id, message);
    }

    private String buildLogLatencyLine(Long latency) {
        LocalDateTime currentTime = LocalDateTime.now();
        String formattedTime = currentTime.format(formatter);
        return String.format("%s,%d", formattedTime, latency);
    }

    @Override
    public void run() {
        running = true;
        var latencyLines = new ArrayList<String>(bufferSize);
        while (running) {
            try {
                if (buffer.isEmpty()) {
                    continue;
                }
                latencyLines.add(this.buildLogLatencyLine(buffer.take()));
                if (latencyLines.size() >= bufferSize) {
                    this.write(latencyLines);
                    latencyLines.clear();
                }
            } catch (InterruptedException ex) {
                this.write(latencyLines);
                this.running = false;
            }
        }
    }

    @Override
    public String getThreadName() {
        return "LATENCY_LOG_WRITER";
    }
}
