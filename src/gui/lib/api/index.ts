import { isServer } from "./../util/environment";

/**
 * Returns the URL of the base API route. On the client side, this is relative. On the server side,
 * it uses http://localhost.
 *
 * @param endpoint The API-root-relative path (without leading slash) of an endpoint for which the
 * URL should be returned. If omitted, the API root URL will be returned.
 */
export function getApiUrl(endpoint: string = "") {
  return `${isServer ? "http://localhost:3000" : ""}/api/v3/${endpoint}`;
}
