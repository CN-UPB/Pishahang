package sonata.kernel.vimadaptor.wrapper.terraform;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.mitchellbosecke.pebble.error.PebbleException;
import org.slf4j.LoggerFactory;
import sonata.kernel.vimadaptor.commons.*;
import sonata.kernel.vimadaptor.wrapper.*;

import java.io.IOException;

abstract public class TerraformWrapper extends ComputeWrapper {

    private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(TerraformWrapper.class);

    /**
     * Terraform client.
     */
    protected TerraformClient terraform;

    /**
     * Constructor.
     *
     * @param config WrapperConfiguration
     */
    public TerraformWrapper(WrapperConfiguration config) {
        super(config);

        this.terraform = new TerraformClient("/root/terraform_data/");
    }

    public void deployFunction(FunctionDeployPayload data, String sid) {
        Logger.error(this.buildLogMessage("Received deploy function call. Ignoring."));
    }

    public void scaleFunction(FunctionScalePayload data, String sid) {
        Logger.error(this.buildLogMessage("Received scale function call. Ignoring."));
    }

    public void deployCloudService(CloudServiceDeployPayload deployPayload, String sid) {
        Logger.info(this.buildLogMessage("Received deploy cloud service call for service " + deployPayload.getServiceInstanceId() + "."));

        TerraformTemplate template = null;
        Logger.info(this.buildLogMessage("Building Kubernetes template for service instance " + deployPayload.getCsd().getInstanceUuid() + "."));
        try {
            template = this.buildTemplate(deployPayload);
        } catch (Exception e) {
            Logger.error(this.buildLogMessage("Failed to build template: " + e.getMessage()));
            this.notifyCloudServiceDeploymentFailed(sid, "Failed to build template");

            return;
        }

        Logger.info(this.buildLogMessage("Building template successful."));
        Logger.info(this.buildLogMessage("Triggering terraform deployment."));

        try {
            this.terraform.forService(deployPayload.getServiceInstanceId())
                    .writeTemplate(template, deployPayload.getCsd().getInstanceUuid())
                    .init(deployPayload.getCsd().getInstanceUuid())
                    .apply(deployPayload.getCsd().getInstanceUuid());
        } catch (TerraformException e) {
            Logger.error(e.getMessage());
            this.notifyCloudServiceDeploymentFailed(sid, "Failed to deploy service using terraform.");

            return;
        } catch (Exception e) {
            Logger.error(this.buildLogMessage("Failed to run terraform command: " +  e.getMessage()));
            this.notifyCloudServiceDeploymentFailed(sid, "Failed to deploy service using terraform.");

            return;
        }

        WrapperBay.getInstance().getVimRepo().writeCloudServiceInstanceEntry(
                deployPayload.getCsd().getInstanceUuid(),
                deployPayload.getServiceInstanceId(),
                this.getConfig().getUuid()
        );
        Logger.info(this.buildLogMessage("Successfully deployed cloud service."));

        this.notifyCloudServiceDeploymentSuccessful(sid, this.getCloudServiceDeployResponse(deployPayload));
    }

    @Deprecated
    public boolean deployService(ServiceDeployPayload data, String callSid) {
        Logger.error(this.buildLogMessage("Received deploy service call. Ignoring."));
        return false;
    }

    public boolean prepareService(String instanceId) throws Exception {
        Logger.info(this.buildLogMessage("Preparing service for instance " + instanceId));

        WrapperBay.getInstance().getVimRepo().writeServiceInstanceEntry(instanceId, instanceId,
                instanceId, this.getConfig().getUuid());

        return true;
    }

    public boolean removeService(String instanceUuid, String callSid) {
        Logger.info(this.buildLogMessage("Received remove service call for service instance " + instanceUuid));

        // Call terraform destroy
        try {
            this.terraform.forService(instanceUuid)
                    .init()
                    .destroy();
        } catch (TerraformException e) {
            Logger.error(e.getMessage());
            this.notifyServiceRemovalFailed(callSid, "Failed to remove service using terraform.");

            return false;
        } catch (Exception e) {
            Logger.error(this.buildLogMessage("Failed to run terraform command: " +  e.getMessage()));
            this.notifyServiceRemovalFailed(callSid, "Failed to remove service using terraform.");

            return false;
        }

        Logger.info(this.buildLogMessage("Removing DB entries for service."));
        WrapperBay.getInstance().getVimRepo().removeServiceInstanceEntry(instanceUuid, this.getConfig().getUuid());

        Logger.info(this.buildLogMessage("Successfully removed service " + instanceUuid + "."));

        this.notifyServiceRemovalSuccessful(callSid);

        return true;
    }

    public boolean isImageStored(VnfImage image, String callSid) {
        Logger.error(this.buildLogMessage("Received is image stored call. Ignoring."));

        return true;
    }

    public void uploadImage(VnfImage image) {
        Logger.error(this.buildLogMessage("Received upload image call. Ignoring."));
    }

    public void removeImage(VnfImage image) {
        Logger.error(this.buildLogMessage("Received remove image call. Ignoring."));
    }

    /**
     * Notify observers that the deployment was successful.
     */
    private void notifyCloudServiceDeploymentSuccessful(String sid, CloudServiceDeployResponse response) {
        try {
            String yaml = TerraformHelpers.transformToYAML(response);
            WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "SUCCESS", yaml);

            this.notifyUpdate(update);
        } catch (JsonProcessingException e) {
            this.notifyCloudServiceDeploymentFailed(sid, "Exception while sending deployment successful message.");
        }
    }

    /**
     * Notify observers that the deployment failed.
     *
     * @param error String
     */
    private void notifyCloudServiceDeploymentFailed(String sid, String error) {
        WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR", error);
        this.notifyUpdate(update);
    }

    /**
     * Notify observers that the service removal was successful.
     */
    private void notifyServiceRemovalSuccessful(String sid) {
        String body =
                "{\"status\":\"COMPLETED\",\"wrapper_uuid\":\"" + this.getConfig().getUuid() + "\"}";
        WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "SUCCESS", body);

        this.notifyUpdate(update);
    }

    /**
     * Notify observers that an error occurred while removing the service.
     *
     * @param error String
     */
    private void notifyServiceRemovalFailed(String sid, String error) {
        WrapperStatusUpdate update = new WrapperStatusUpdate(sid, "ERROR", error);
        this.notifyUpdate(update);
    }

    /**
     * Propagate status update to observers.
     *
     * @param update WrapperStatusUpdate
     */
    protected void notifyUpdate(WrapperStatusUpdate update) {
        this.markAsChanged();
        this.notifyObservers(update);
    }

    /**
     * Build a log message with the wrapper's name.
     *
     * @param message String
     *
     * @return String
     */
    protected String buildLogMessage(String message) {
        return String.format("[%s] %s", this.getWrapperName(), message);
    }

    @Override
    public abstract ResourceUtilisation getResourceUtilisation();

    /**
     * Build the terraform deployment template.
     *
     * @param data CloudServiceDeployPayload
     *
     * @return TerraformTemplate
     */
    public abstract TerraformTemplate buildTemplate(CloudServiceDeployPayload data) throws IOException, PebbleException;

    /**
     * Get the deploy response from the deploy payload.
     *
     * @param payload CloudServiceDeployPayload
     *
     * @return CloudServiceDeployResponse
     */
    protected abstract CloudServiceDeployResponse getCloudServiceDeployResponse(CloudServiceDeployPayload payload);

    /**
     * Get the wrapper's name.
     *
     * @return String
     */
    protected abstract String getWrapperName();
}
