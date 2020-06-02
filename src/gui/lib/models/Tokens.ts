/**
 * Stores a JWT access token and a refresh token, as well as their expiry timestamps
 */
export interface Tokens {
  /** JWT access token */
  accessToken: string;

  /** Unix timestamp of the moment the access token expires */
  accessTokenExpiresAt: number;

  /** JWT refresh token */
  refreshToken: string;

  /** Unix timestamp of the moment the refresh token expires */
  refreshTokenExpiresAt: number;
}
