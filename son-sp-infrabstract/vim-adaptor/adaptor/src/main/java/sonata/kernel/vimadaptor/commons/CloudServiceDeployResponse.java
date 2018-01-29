package sonata.kernel.vimadaptor.commons;

import com.fasterxml.jackson.annotation.JsonProperty;
import sonata.kernel.vimadaptor.commons.csr.CsRecord;

public class CloudServiceDeployResponse {
    private String instanceName;

    private String instanceVimUuid;

    private String message;

    @JsonProperty("request_status")
    private String requestStatus;

    private String vimUuid;

    private CsRecord csr;


    public String getInstanceName() {
        return instanceName;
    }

    public String getInstanceVimUuid() {
        return instanceVimUuid;
    }

    public String getMessage() {
        return message;
    }

    public String getRequestStatus() {
        return requestStatus;
    }

    public String getVimUuid() {
        return vimUuid;
    }

    public CsRecord getCsr() {
        return csr;
    }

    public void setInstanceName(String instanceName) {
        this.instanceName = instanceName;
    }

    public void setInstanceVimUuid(String instanceVimUuid) {
        this.instanceVimUuid = instanceVimUuid;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public void setRequestStatus(String requestStatus) {
        this.requestStatus = requestStatus;
    }

    public void setVimUuid(String vimUuid) {
        this.vimUuid = vimUuid;
    }

    public void setCsr(CsRecord csr) {
        this.csr = csr;
    }
}
