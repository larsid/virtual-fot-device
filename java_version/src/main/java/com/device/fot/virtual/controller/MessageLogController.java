package com.device.fot.virtual.controller;


import com.device.fot.virtual.model.Data;
import java.util.ArrayList;

public class MessageLogController extends FilePersistenceController<Data> {

    private static MessageLogController messageLogController = new MessageLogController();

    private MessageLogController() {
        super("messages_log.csv");
    }

    public synchronized static MessageLogController getInstance() {
        return messageLogController;
    }

    public void putData(Data data) throws InterruptedException {
        if (canSaveData) {
            this.buffer.put(data);
        }
    }

    @Override
    public void run() {
        running = true;
        var dataLines = new ArrayList<String>(bufferSize);
        while (running) {
            try {
                if (!this.buffer.isEmpty()) {
                    dataLines.add(this.buffer.take().toString());
                    if (dataLines.size() >= bufferSize) {
                        this.write(dataLines);
                        dataLines.clear();
                    }
                }
            } catch (InterruptedException ex) {
                this.write(dataLines);
                this.running = false;
            }
        }
    }

    @Override
    public String getThreadName() {
        return "MESSAGE_LOG_WRITER";
    }
}
