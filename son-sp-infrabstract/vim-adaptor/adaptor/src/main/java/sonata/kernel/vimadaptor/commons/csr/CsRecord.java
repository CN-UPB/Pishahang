package sonata.kernel.vimadaptor.commons.csr;

import com.fasterxml.jackson.annotation.JsonProperty;
import sonata.kernel.vimadaptor.commons.Status;
import sonata.kernel.vimadaptor.commons.csr.VduRecord;

import java.util.ArrayList;

public class CsRecord {
    @JsonProperty("id")
    private String id;

    @JsonProperty("descriptor_reference")
    private String descriptorReference;

    @JsonProperty("descriptor_version")
    private String descriptorVersion;

    private Status status;

    @JsonProperty("virtual_deployment_units")
    private ArrayList<VduRecord> virtualDeploymentUnits;

    public CsRecord() {
        this.virtualDeploymentUnits = new ArrayList<VduRecord>();
    }

    public void addVdu(VduRecord unit) {
        this.virtualDeploymentUnits.add(unit);
    }

    public String getDescriptorReference() {
        return descriptorReference;
    }

    public String getDescriptorVersion() {
        return descriptorVersion;
    }

    public String getId() {
        return id;
    }

    public Status getStatus() {
        return status;
    }

    public ArrayList<VduRecord> getVirtualDeploymentUnits() {
        return virtualDeploymentUnits;
    }

    public void setDescriptorReference(String descriptorReference) {
        this.descriptorReference = descriptorReference;
    }

    public void setDescriptorVersion(String descriptorVersion) {
        this.descriptorVersion = descriptorVersion;
    }

    public void setId(String id) {
        this.id = id;
    }

    public void setStatus(Status status) {
        this.status = status;
    }

    public void setVirtualDeploymentUnits(ArrayList<VduRecord> virtualDeploymentUnits) {
        this.virtualDeploymentUnits = virtualDeploymentUnits;
    }

    @Override
    public boolean equals(Object obj) {
        if (obj instanceof CsRecord) {
            CsRecord temp = (CsRecord) obj;
            return temp.getId().equals(this.getId());
        } else {
            return false;
        }
    }
}
