
package sonata.kernel.vimadaptor.wrapper.sp.client.model;

import java.util.HashMap;import java.util.Map;import com.fasterxml.jackson.annotation.JsonAnyGetter;import com.fasterxml.jackson.annotation.JsonAnySetter;import com.fasterxml.jackson.annotation.JsonIgnore;import com.fasterxml.jackson.annotation.JsonInclude;import com.fasterxml.jackson.annotation.JsonProperty;import com.fasterxml.jackson.annotation.JsonPropertyOrder;


@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonPropertyOrder({"status", "count", "items"})
public class VimRequestStatus {

  @JsonProperty("status")
  private Integer status;
  @JsonProperty("count")
  private Integer count;
  @JsonProperty("items")
  private VimRequestStatusItem items;
  @JsonIgnore
  private Map<String, Object> additionalProperties = new HashMap<String, Object>();

  @JsonProperty("status")
  public Integer getStatus() {
    return status;
  }

  @JsonProperty("status")
  public void setStatus(Integer status) {
    this.status = status;
  }

  @JsonProperty("count")
  public Integer getCount() {
    return count;
  }

  @JsonProperty("count")
  public void setCount(Integer count) {
    this.count = count;
  }

  @JsonProperty("items")
  public VimRequestStatusItem getItems() {
    return items;
  }

  @JsonProperty("items")
  public void setItems(VimRequestStatusItem items) {
    this.items = items;
  }

  @JsonAnyGetter
  public Map<String, Object> getAdditionalProperties() {
    return this.additionalProperties;
  }

  @JsonAnySetter
  public void setAdditionalProperty(String name, Object value) {
    this.additionalProperties.put(name, value);
  }

}
