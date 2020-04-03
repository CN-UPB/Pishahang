package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

public class CsDescriptor {

    private String uuid;

    @JsonProperty("descriptor_version")
    private String descriptorVersion;

    private String vendor;

    private String name;

    private String version;

    private String author;

    private String description;

    @JsonProperty("instance_uuid")
    private String instanceUuid;

    @JsonProperty("virtual_deployment_units")
    private ArrayList<VirtualDeploymentUnit> virtualDeploymentUnits;

    public String getDescriptorVersion() {
        return descriptorVersion;
    }

    public void setDescriptorVersion(String descriptorVersion) {
        this.descriptorVersion = descriptorVersion;
    }

    public String getVendor() {
        return vendor;
    }

    public void setVendor(String vendor) {
        this.vendor = vendor;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public ArrayList<VirtualDeploymentUnit> getVirtualDeploymentUnits() {
        return virtualDeploymentUnits;
    }

    public void setVirtualDeploymentUnits(ArrayList<VirtualDeploymentUnit> virtualDeploymentUnits) {
        this.virtualDeploymentUnits = virtualDeploymentUnits;
    }

    public String getUuid() {
        return uuid;
    }

    public void setUuid(String uuid) {
        this.uuid = uuid;
    }

    public String getInstanceUuid() {
        return instanceUuid;
    }

    public void setInstanceUuid(String instanceUuid) {
        this.instanceUuid = instanceUuid;
    }
}
