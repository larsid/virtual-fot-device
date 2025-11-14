package com.device.fot.virtual.controller;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author Uellington Damasceno
 */
public abstract class FilePersistenceController<T> implements Runnable {

    protected int bufferSize = 64;
    protected boolean running = false, canSaveData = false;
    protected Thread thread;
    protected String fileName;
    protected LinkedBlockingQueue<T> buffer = new LinkedBlockingQueue<>();
    protected StandardOpenOption fileOpenOption;
    private static final Logger logger = Logger.getLogger(FilePersistenceController.class.getName());
    
    protected FilePersistenceController(String fileName) {
        this.fileName = fileName;
    }
    
    public abstract String getThreadName();
    
    public void start() {
        if (this.thread == null || !running) {
            this.thread = new Thread(this);
            this.thread.setDaemon(true);
            this.thread.setName(this.getThreadName());
            this.thread.start();
        }
    }

    public void setCanSaveData(boolean canSaveData) {
        this.canSaveData = canSaveData;
    }

   public void createAndUpdateFileName(String fileName) throws IOException {
        File expDirectory = new File("exp");

        if (!expDirectory.exists()) {
            expDirectory.mkdir();
            logger.info("Diretório 'exp' criado.");
        }

        File file = new File(expDirectory, fileName);

        if (!file.exists()) {
            file.createNewFile();
            this.fileOpenOption = StandardOpenOption.WRITE;
            logger.log(Level.INFO, "Arquivo criado: {0}", file.getAbsolutePath());
        } else {
            this.fileOpenOption = StandardOpenOption.APPEND;
            logger.log(Level.INFO, "O arquivo j\u00e1 existe: {0}", file.getAbsolutePath());
        }

        this.fileName = file.getAbsolutePath();
    }

    protected void write(List<String> lines) {
        try (var w = Files.newBufferedWriter(Path.of(this.fileName), this.fileOpenOption)) {
            lines.forEach(line -> {
                try {
                    w.write(line);
                    w.newLine();
                    logger.info(line);
                } catch (IOException ex) {
                    logger.log(Level.SEVERE, null, ex);
                }
            });
        } catch (IOException ex) {
           logger.log(Level.SEVERE, null, ex);
        }
    }

    public void stop() {
        running = false;
    }
}
