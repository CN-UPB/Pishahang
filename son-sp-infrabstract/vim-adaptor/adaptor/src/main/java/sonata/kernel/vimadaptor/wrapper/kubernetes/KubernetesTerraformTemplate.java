package sonata.kernel.vimadaptor.wrapper.kubernetes;

import org.json.JSONObject;
import org.json.JSONTokener;
import sonata.kernel.vimadaptor.commons.csd.CsDescriptor;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;
import sonata.kernel.vimadaptor.wrapper.terraform.TerraformTemplate;

import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

public class KubernetesTerraformTemplate extends TerraformTemplate {

    private CsDescriptor csd;

    private WrapperConfiguration wrapper;

    private String serviceInstanceId;

    @Override
    public String getMainTemplate() {
        return "templates/kubernetes/main.tf";
    }

    @Override
    public String getServiceTemplate() {
        return "templates/kubernetes/cloud_service.tf";
    }

    @Override
    public Map<String, Object> getContext() {
        Map<String, Object> context = new HashMap<>();
        context.put("serviceId", this.csd.getInstanceUuid());
        context.put("serviceInstanceId", this.serviceInstanceId);
        context.put("csd", this.csd);
        context.put("endpoint", String.format("https://%s", wrapper.getVimEndpoint()));
        context.put("token", wrapper.getAuthPass());
        context.put("caCert", new String(Base64.getDecoder().decode(this.getComputeConfigurationValue("cluster_ca_cert"))));

        return context;
    }

    public KubernetesTerraformTemplate withCsd(CsDescriptor csd) {
        this.csd = csd;

        return this;
    }

    public KubernetesTerraformTemplate withWrapperConfiguration(WrapperConfiguration wrapper) {
        this.wrapper = wrapper;

        return this;
    }

    public KubernetesTerraformTemplate forService(String serviceInstanceId) {
        this.serviceInstanceId = serviceInstanceId;

        return this;
    }

    /**
     * Get a value from the dynamic compute configuration of the wrapper config.
     *
     * @param key String
     *
     * @return String
     */
    private String getComputeConfigurationValue(String key) {
        JSONTokener tokener = new JSONTokener(this.wrapper.getConfiguration());
        JSONObject object = (JSONObject) tokener.nextValue();

        return object.getString(key);
    }
}
