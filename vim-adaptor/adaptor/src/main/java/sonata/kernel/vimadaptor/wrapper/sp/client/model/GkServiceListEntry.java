package sonata.kernel.vimadaptor.wrapper.sp.client.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;

public class GkServiceListEntry {

  @JsonProperty("created_at")
  private String createdAt;
  @JsonProperty("md5")
  private String md5;
  @JsonProperty("nsd")
  private ServiceDescriptor nsd;
  @JsonProperty("signature")
  private String signature;
  @JsonProperty("status")
  private String status;
  @JsonProperty("updated_at")
  private String updatedAt;
  @JsonProperty("username")
  private String username;
  @JsonProperty("uuid")
  private String uuid;
  @JsonProperty("user_licence")
  private String userLicence;

  public String getCreatedAt() {
    return createdAt;
  }

  public String getMd5() {
    return md5;
  }

  public ServiceDescriptor getNsd() {
    return nsd;
  }

  public String getSignature() {
    return signature;
  }

  public String getStatus() {
    return status;
  }

  public String getUpdatedAt() {
    return updatedAt;
  }

  public String getUsername() {
    return username;
  }

  public String getUuid() {
    return uuid;
  }

  public String getUserLicence() {
    return userLicence;
  }

  public void setCreatedAt(String createdAt) {
    this.createdAt = createdAt;
  }

  public void setMd5(String md5) {
    this.md5 = md5;
  }

  public void setNsd(ServiceDescriptor nsd) {
    this.nsd = nsd;
  }

  public void setSignature(String signature) {
    this.signature = signature;
  }

  public void setStatus(String status) {
    this.status = status;
  }

  public void setUpdatedAt(String updatedAt) {
    this.updatedAt = updatedAt;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  public void setUuid(String uuid) {
    this.uuid = uuid;
  }

  public void setUserLicence(String userLicence) {
    this.userLicence = userLicence;
  }


}
