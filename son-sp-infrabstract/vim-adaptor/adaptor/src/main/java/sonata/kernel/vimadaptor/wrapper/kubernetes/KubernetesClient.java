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

public class KubernetesClient {

    private static final String RESOURCE_UTILISATION_ENDPOINT = "%s/apis/metrics.k8s.io/v1beta1/nodes";

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
            totalMemory += Integer.parseInt(node.getStatus().getAllocatable().get("memory").getAmount().replaceAll("\\D+","")) / 1024;
            cpuCores += Integer.parseInt(node.getStatus().getAllocatable().get("cpu").getAmount().replaceAll("\\D+",""));
        }

        JsonNode response = this.makeHttpRequest(String.format(RESOURCE_UTILISATION_ENDPOINT, this.endpoint));
        System.out.println(response.asText());
        JsonNode metrics = response.get("items");

        for (int i = 0; i < metrics.size(); i++) {
            JsonNode usage = metrics.get(i).get("usage");

            cpuLoad += Integer.parseInt(usage.get("cpu").asText().replaceAll("\\D+",""));
            usedMemory += Integer.parseInt(usage.get("memory").asText().replaceAll("\\D+","")) / 1024;
        }

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
                .withTrustCerts(true)
                .withOauthToken(this.token).build();

        return new DefaultKubernetesClient(config);
    }
}
