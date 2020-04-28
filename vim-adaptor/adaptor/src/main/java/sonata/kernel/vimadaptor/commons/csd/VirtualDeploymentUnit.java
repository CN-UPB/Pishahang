package sonata.kernel.vimadaptor.commons.csd;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;

public class VirtualDeploymentUnit {

    private String id;

    private String name;

    private String description;

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

    public void setId(String id) {
        this.id = id;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
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

    public ResourceRequirements getResourceRequirements() {
        return resourceRequirements;
    }

    public void setResourceRequirements(ResourceRequirements resourceRequirements) {
        this.resourceRequirements = resourceRequirements;
    }

    public ScalingConfiguration getScalingConfiguration() {
        return scalingConfiguration;
    }

    public void setScalingConfiguration(ScalingConfiguration scalingConfiguration) {
        this.scalingConfiguration = scalingConfiguration;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public ArrayList<EnvironmentVariable> getEnvironmentVariables() {
        return environmentVariables != null ? environmentVariables : new ArrayList<EnvironmentVariable>();
    }

    public void setEnvironmentVariables(ArrayList<EnvironmentVariable> environmentVariables) {
        this.environmentVariables = environmentVariables;
    }
}
