package sonata.kernel.vimadaptor.commons;

import com.fasterxml.jackson.annotation.JsonProperty;
import sonata.kernel.vimadaptor.commons.csd.CsDescriptor;

public class CloudServiceDeployPayload {
    @JsonProperty("service_instance_id")
    private String serviceInstanceId;
    @JsonProperty("vim_uuid")
    private String vimUuid;
    @JsonProperty("csd")
    private CsDescriptor csd;

    public String getServiceInstanceId() {
        return serviceInstanceId;
    }

    public String getVimUuid() {
        return vimUuid;
    }

    public CsDescriptor getCsd() {
        return csd;
    }

    public void setServiceInstanceId(String serviceInstanceId) {
        this.serviceInstanceId = serviceInstanceId;
    }

    public void setVimUuid(String vimUuid) {
        this.vimUuid = vimUuid;
    }

    public void setCsd(CsDescriptor csd) {
        this.csd = csd;
    }
}
