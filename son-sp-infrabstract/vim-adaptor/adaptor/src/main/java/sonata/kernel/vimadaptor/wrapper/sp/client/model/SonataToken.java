package sonata.kernel.vimadaptor.wrapper.sp.client.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class SonataToken {

  @JsonProperty("access_token")
  private String token;
  @JsonProperty("token_type")
  private String type;
  @JsonProperty("not-before-policy")
  private int policy;
  @JsonProperty("session_state")
  private String sessionState;
  @JsonProperty("expires_in")
  private int expiresIn;
  @JsonProperty("refresh_expires_in")
  private int refreshExpiresIn;
  @JsonProperty("refresh_token")
  private String refreshToken;
  
  public String getToken() {
    return token;
  }

  public String getType() {
    return type;
  }

  public int getPolicy() {
    return policy;
  }

  public String getSessionState() {
    return sessionState;
  }

  public void setToken(String token) {
    this.token = token;
  }

  public void setType(String type) {
    this.type = type;
  }

  public void setSessionState(String sessionState) {
    this.sessionState = sessionState;
  }

  public int getExpiresIn() {
    return expiresIn;
  }

  public int getRefreshExpiresIn() {
    return refreshExpiresIn;
  }

  public String getRefreshToken() {
    return refreshToken;
  }

  public void setPolicy(int policy) {
    this.policy = policy;
  }

  public void setExpiresIn(int expiresIn) {
    this.expiresIn = expiresIn;
  }

  public void setRefreshExpiresIn(int refreshExpiresIn) {
    this.refreshExpiresIn = refreshExpiresIn;
  }

  public void setRefreshToken(String refreshToken) {
    this.refreshToken = refreshToken;
  }

}
