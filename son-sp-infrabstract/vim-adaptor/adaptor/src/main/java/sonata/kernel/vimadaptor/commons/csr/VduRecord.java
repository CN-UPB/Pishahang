package sonata.kernel.vimadaptor.commons.csr;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import sonata.kernel.vimadaptor.commons.VnfcInstance;
import sonata.kernel.vimadaptor.commons.csd.EnvironmentVariable;
import sonata.kernel.vimadaptor.commons.csd.Port;
import sonata.kernel.vimadaptor.commons.csd.ResourceRequirements;
import sonata.kernel.vimadaptor.commons.csd.ScalingConfiguration;

import java.util.ArrayList;

@JsonIgnoreProperties(ignoreUnknown = true)
public class VduRecord {
    private String id;

    @JsonProperty("number_of_instances")
    private int numberOfInstances;

    @JsonProperty("vdu_reference")
    private String vduReference;

    @JsonProperty("vim_id")
    private String vimId;

    @JsonProperty("service_image")
    private String serviceImage;

    @JsonProperty("service_name")
    private String serviceName;

    @JsonProperty("service_type")
    private String serviceType;

    @JsonProperty("service_ports")
    private ArrayList<Port> servicePorts;

    @JsonProperty("resource_requirements")
    private ResourceRequirements resourceRequirements;

    @JsonProperty("scale_in_out")
    private ScalingConfiguration scalingConfiguration;

    @JsonProperty("environment")
    private ArrayList<EnvironmentVariable> environmentVariables;

    public String getId() {
        return id;
    }

    public int getNumberOfInstances() {
        return numberOfInstances;
    }

    public ResourceRequirements getResourceRequirements() {
        return resourceRequirements;
    }

    public String getVduReference() {
        return vduReference;
    }

    public void setId(String id) {
        this.id = id;
    }

    public void setNumberOfInstances(int numberOfInstances) {
        this.numberOfInstances = numberOfInstances;
    }

    public void setResourceRequirements(ResourceRequirements resourceRequirements) {
        this.resourceRequirements = resourceRequirements;
    }

    public void setVduReference(String vduReference) {
        this.vduReference = vduReference;
    }

    public String getVimId() {
        return vimId;
    }

    public void setVimId(String vimId) {
        this.vimId = vimId;
    }

    public String getServiceImage() {
        return serviceImage;
    }

    public void setServiceImage(String serviceImage) {
        this.serviceImage = serviceImage;
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getServiceType() {
        return serviceType;
    }

    public void setServiceType(String serviceType) {
        this.serviceType = serviceType;
    }

    public ArrayList<Port> getServicePorts() {
        return servicePorts;
    }

    public void setServicePorts(ArrayList<Port> servicePorts) {
        this.servicePorts = servicePorts;
    }

    public ScalingConfiguration getScalingConfiguration() {
        return scalingConfiguration;
    }

    public void setScalingConfiguration(ScalingConfiguration scalingConfiguration) {
        this.scalingConfiguration = scalingConfiguration;
    }

    public ArrayList<EnvironmentVariable> getEnvironmentVariables() {
        return environmentVariables;
    }

    public void setEnvironmentVariables(ArrayList<EnvironmentVariable> environmentVariables) {
        this.environmentVariables = environmentVariables;
    }
}
