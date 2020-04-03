package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

public class Port {

    private String name;

    private String protocol;

    private int port;

    @JsonProperty("target_port")
    private int targetPort;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getProtocol() {
        return protocol;
    }

    public void setProtocol(String protocol) {
        this.protocol = protocol;
    }

    public int getPort() {
        return port;
    }

    public void setPort(int port) {
        this.port = port;
    }

    public int getTargetPort() {
        return targetPort;
    }

    public void setTargetPort(int targetPort) {
        this.targetPort = targetPort;
    }
}
