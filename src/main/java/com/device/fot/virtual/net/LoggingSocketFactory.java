package com.device.fot.virtual.net;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketAddress;
import java.net.SocketOption;
import java.nio.channels.SocketChannel;
import java.util.Objects;
import java.util.Set;
import java.util.logging.Logger;
import javax.net.SocketFactory;

/**
 * SocketFactory implementation that logs the local address chosen when the MQTT client creates a
 * TCP connection. The factory returns sockets that print the source and destination pair once the
 * underlying socket successfully connects.
 */
public final class LoggingSocketFactory extends SocketFactory {

    private static final Logger LOGGER = Logger.getLogger(LoggingSocketFactory.class.getName());

    private final String deviceId;

    private LoggingSocketFactory(String deviceId) {
        this.deviceId = Objects.requireNonNull(deviceId, "deviceId");
    }

    public static SocketFactory forDevice(String deviceId) {
        return new LoggingSocketFactory(deviceId);
    }

    @Override
    public Socket createSocket() {
        return new LoggingSocket(deviceId);
    }

    @Override
    public Socket createSocket(String host, int port) throws IOException {
        LoggingSocket socket = new LoggingSocket(deviceId);
        socket.connect(new InetSocketAddress(host, port));
        return socket;
    }

    @Override
    public Socket createSocket(String host, int port, InetAddress localAddress, int localPort)
            throws IOException {
        LoggingSocket socket = new LoggingSocket(deviceId);
        if (localAddress != null || localPort > 0) {
            socket.bind(new InetSocketAddress(localAddress, localPort));
        }
        socket.connect(new InetSocketAddress(host, port));
        return socket;
    }

    @Override
    public Socket createSocket(InetAddress host, int port) throws IOException {
        LoggingSocket socket = new LoggingSocket(deviceId);
        socket.connect(new InetSocketAddress(host, port));
        return socket;
    }

    @Override
    public Socket createSocket(InetAddress address, int port, InetAddress localAddress, int localPort)
            throws IOException {
        LoggingSocket socket = new LoggingSocket(deviceId);
        if (localAddress != null || localPort > 0) {
            socket.bind(new InetSocketAddress(localAddress, localPort));
        }
        socket.connect(new InetSocketAddress(address, port));
        return socket;
    }

    private static final class LoggingSocket extends Socket {

        private final String deviceId;

        private LoggingSocket(String deviceId) {
            super();
            this.deviceId = deviceId;
        }

        @Override
        public void connect(SocketAddress endpoint) throws IOException {
            super.connect(endpoint);
            logConnection(endpoint);
        }

        @Override
        public void connect(SocketAddress endpoint, int timeout) throws IOException {
            super.connect(endpoint, timeout);
            logConnection(endpoint);
        }

        private void logConnection(SocketAddress endpoint) {
            if (!(endpoint instanceof InetSocketAddress)) {
                return;
            }
            InetSocketAddress inetEndpoint = (InetSocketAddress) endpoint;
            InetAddress local = getLocalAddress();
            String localIp = local != null ? local.getHostAddress() : "unknown";
            int localPort = getLocalPort();
            InetAddress remote = inetEndpoint.getAddress();
            String remoteIp = remote != null ? remote.getHostAddress() : inetEndpoint.getHostString();
            int remotePort = inetEndpoint.getPort();
            LOGGER.info(() ->
                    String.format(
                            "Device %s established MQTT connection %s:%d -> %s:%d",
                            deviceId, localIp, localPort, remoteIp, remotePort));
        }

        @Override
        public SocketChannel getChannel() {
            return super.getChannel();
        }

        @Override
        public <T> Socket setOption(SocketOption<T> name, T value) throws IOException {
            return super.setOption(name, value);
        }

        @Override
        public <T> T getOption(SocketOption<T> name) throws IOException {
            return super.getOption(name);
        }

        @Override
        public Set<SocketOption<?>> supportedOptions() {
            return super.supportedOptions();
        }

        @Override
        public void bind(SocketAddress bindpoint) throws IOException {
            super.bind(bindpoint);
        }

        @Override
        public void close() throws IOException {
            super.close();
        }

        @Override
        public java.io.InputStream getInputStream() throws IOException {
            return super.getInputStream();
        }

        @Override
        public java.io.OutputStream getOutputStream() throws IOException {
            return super.getOutputStream();
        }
    }
}
