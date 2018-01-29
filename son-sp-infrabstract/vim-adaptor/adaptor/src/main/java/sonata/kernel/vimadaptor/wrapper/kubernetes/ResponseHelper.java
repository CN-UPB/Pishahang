package sonata.kernel.vimadaptor.wrapper.kubernetes;

import sonata.kernel.vimadaptor.commons.CloudServiceDeployPayload;
import sonata.kernel.vimadaptor.commons.CloudServiceDeployResponse;
import sonata.kernel.vimadaptor.commons.csr.CsRecord;
import sonata.kernel.vimadaptor.commons.Status;
import sonata.kernel.vimadaptor.commons.csd.CsDescriptor;
import sonata.kernel.vimadaptor.commons.csd.VirtualDeploymentUnit;
import sonata.kernel.vimadaptor.commons.csr.VduRecord;
import sonata.kernel.vimadaptor.wrapper.WrapperBay;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;

public class ResponseHelper {

    private WrapperConfiguration wrapper;

    public ResponseHelper(WrapperConfiguration wrapper) {
        this.wrapper = wrapper;
    }

    /**
     * Build the response from the given data.
     *
     * @return CloudServiceDeployResponse
     */
    public CloudServiceDeployResponse buildDeployResponse(CloudServiceDeployPayload deployPayload) {
        CloudServiceDeployResponse response = new CloudServiceDeployResponse();
        response.setRequestStatus("COMPLETED");
        response.setInstanceVimUuid(WrapperBay.getInstance().getVimRepo().getServiceInstanceVimUuid(deployPayload.getServiceInstanceId(), this.wrapper.getUuid()));
        response.setInstanceName(WrapperBay.getInstance().getVimRepo().getServiceInstanceVimName(deployPayload.getServiceInstanceId(), this.wrapper.getUuid()));
        response.setVimUuid(this.wrapper.getUuid());
        response.setMessage("");

        CsDescriptor csd = deployPayload.getCsd();

        CsRecord csr = new CsRecord();
        csr.setDescriptorVersion("csr-schema-01");
        csr.setDescriptorReference(csd.getUuid());
        csr.setId(csd.getInstanceUuid());
        csr.setStatus(Status.normal_operation);

        for (VirtualDeploymentUnit vdu : csd.getVirtualDeploymentUnits()) {
            VduRecord vdur = new VduRecord();
            vdur.setId(vdu.getId());
            vdur.setNumberOfInstances(1);
            vdur.setVduReference(csd.getName() + ":" + vdu.getId());
            vdur.setVimId(this.wrapper.getUuid());
            vdur.setServiceImage(vdu.getServiceImage());
            vdur.setServiceName(vdu.getServiceName());
            vdur.setServiceType(vdu.getServiceType());
            vdur.setServicePorts(vdu.getServicePorts());
            vdur.setResourceRequirements(vdu.getResourceRequirements());
            vdur.setEnvironmentVariables(vdu.getEnvironmentVariables());
            csr.addVdu(vdur);
        }

        response.setCsr(csr);

        return response;
    }
}
