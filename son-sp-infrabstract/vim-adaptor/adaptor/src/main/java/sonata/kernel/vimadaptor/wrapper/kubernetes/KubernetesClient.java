package sonata.kernel.vimadaptor.wrapper.kubernetes;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.fabric8.kubernetes.api.model.Node;
import io.fabric8.kubernetes.api.model.NodeList;
import io.fabric8.kubernetes.client.Config;
import io.fabric8.kubernetes.client.ConfigBuilder;
import io.fabric8.kubernetes.client.DefaultKubernetesClient;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import org.json.JSONObject;
import org.json.JSONTokener;
import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;

import java.io.IOException;
import java.util.Base64;
import java.util.Objects;

public class KubernetesClient {

    private static final String RESOURCE_UTILISATION_ENDPOINT = "%s/api/v1/namespaces/kube-system/services/kubernetes-dashboard/proxy/api/v1/node/%s";

    private WrapperConfiguration config;

    private String endpoint;
    private String token;
    private String caCertData;

    private io.fabric8.kubernetes.client.KubernetesClient kubernetesClient;
    private OkHttpClient httpClient;

    public KubernetesClient(WrapperConfiguration config) {
        this.config = config;

        this.endpoint = String.format("https://%s", config.getVimEndpoint());
        this.token = config.getAuthPass();
        this.caCertData = new String(Base64.getDecoder().decode(this.getComputeConfigurationValue("cluster_ca_cert")));
        this.kubernetesClient = this.getKubernetesClient();
        this.httpClient = HttpClientBuilder.buildClient(this.caCertData);
    }

    /**
     * Fetch a list of all nodes of the cluster.
     *
     * @return NodeList
     */
    public NodeList fetchNodes() {
        return this.kubernetesClient.nodes().list();
    }

    /**
     * Get the cumulative resource utilisation of the cluster.
     *
     * @param nodes NodeList
     *
     * @return ResourceUtilisation
     */
    public ResourceUtilisation getClusterResourceUtilisation(NodeList nodes) throws IOException {
        int totalMemory = 0;
        int usedMemory = 0;
        int cpuCores = 0;
        int cpuLoad = 0;

        for (Node node : nodes.getItems()) {
            ResourceUtilisation nodeUtilisation = this.getNodeResourceUtilisation(node);

            totalMemory += nodeUtilisation.getTotMemory();
            usedMemory += nodeUtilisation.getUsedMemory();
            cpuCores += nodeUtilisation.getTotCores();
            cpuLoad += nodeUtilisation.getUsedCores();
        }

        return new ResourceUtilisation(cpuCores, totalMemory, cpuLoad, usedMemory);
    }

    /**
     * Get the resource utilisation for the node.
     *
     * @param node Node
     *
     * @return ResourceUtilisation
     */
    public ResourceUtilisation getNodeResourceUtilisation(Node node) throws IOException {
        JsonNode response = this.makeHttpRequest(String.format(RESOURCE_UTILISATION_ENDPOINT, this.endpoint, node.getMetadata().getName()));
        JsonNode metrics = response.get("metrics");

        int totalMemory = 0;
        int usedMemory = 0;
        int cpuCores = 0;
        int cpuLoad = 0;

        for (int i = 0; i < metrics.size(); i++) {
            JsonNode metric = metrics.get(i);
            JsonNode dataPoints = metric.get("dataPoints");

            if (Objects.equals(metric.get("metricName").asText(), "cpu/usage_rate")) {
                cpuLoad += dataPoints.get(dataPoints.size() - 1).get("y").asInt();
            } else if (Objects.equals(metric.get("metricName").asText(), "memory/usage")) {
                usedMemory += dataPoints.get(dataPoints.size() - 1).get("y").asLong() / 1024 / 1024;
            }
        }

        JsonNode resources = response.get("allocatedResources");
        totalMemory += resources.get("memoryCapacity").asLong() / 1024 / 1024;
        cpuCores += resources.get("cpuCapacity").asInt();

        return new ResourceUtilisation(cpuCores, totalMemory, cpuLoad, usedMemory);
    }

    /**
     * Get a value from the dynamic compute configuration of the wrapper config.
     *
     * @param key String
     *
     * @return String
     */
    private String getComputeConfigurationValue(String key) {
        JSONTokener tokener = new JSONTokener(this.config.getConfiguration());
        JSONObject object = (JSONObject) tokener.nextValue();

        return object.getString(key);
    }

    /**
     * Make an HTTP request to the given url.
     *
     * @param url String
     *
     * @return JsonNode
     * @throws IOException
     */
    private JsonNode makeHttpRequest(String url) throws IOException {
        Request request = this.buildHttpRequest(url);
        Response response = this.httpClient.newCall(request).execute();

        return this.parseJsonResponse(response.body().string());
    }

    /**
     * Turn an HTTP response into a json object.
     *
     * @param json String
     *
     * @return JsonNode
     * @throws IOException
     */
    private JsonNode parseJsonResponse(String json) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        JsonFactory factory = mapper.getFactory();
        JsonParser parser = factory.createParser(json);

        return mapper.readTree(parser);
    }

    /**
     * Build an HTTP request with authorization header.
     *
     * @param url String
     *
     * @return Request
     */
    private Request buildHttpRequest(String url) {
        return new Request.Builder()
                .url(url)
                .addHeader("Authorization", String.format("Bearer %s", this.token))
                .build();
    }

    /**
     * @return DefaultKubernetesClient
     */
    private DefaultKubernetesClient getKubernetesClient() {
        // TODO: fix withTrustCerts
        Config config = new ConfigBuilder().withMasterUrl(this.endpoint)
                .withCaCertData(this.caCertData)
                .withTrustCerts(true)
                .withOauthToken(this.token).build();

        return new DefaultKubernetesClient(config);
    }
}
