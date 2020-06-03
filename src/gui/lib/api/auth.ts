import axios, { AxiosError, AxiosRequestConfig, AxiosResponse, Method } from "axios";

import { ApiReply } from "./../models/ApiReply";
import { Tokens } from "../models/Tokens";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "./endpoints";
import { getApiUrl } from "./index";

export class NullTokenError extends Error {
  constructor() {
    super("No authorization token is provided.");
  }
}

/**
 * Sends a login request to the API
 *
 * @param username The username to be submitted
 * @param password The password to be submitted
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure. In case of
 * success, the resulting `Session` object is provided via the `payload` attribute.
 */
export async function login(username: string, password: string): Promise<ApiReply<Tokens>> {
  try {
    const now = Math.round(Date.now() / 1000);
    const replyData = (await axios.post(getApiUrl("auth"), { username, password })).data;
    return {
      success: true,
      payload: {
        accessToken: replyData.accessToken,
        refreshToken: replyData.refreshToken,
        accessTokenExpiresAt: now + replyData.accessTokenExpiresIn,
        refreshTokenExpiresAt: now + replyData.refreshTokenExpiresIn,
      },
    };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 401:
        return { success: false, message: "Invalid username or password" };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}

/**
 * Performs an HTTP request using axios and sets an `Authorization` header with the provided token.
 * In case of authorization failure (when the server returns status code 401), the onAuthError
 * method is invoked.
 *
 * @param method The request method
 * @param url The request URL
 * @param token The auth token to be used
 * @param onAuthError A function that is invoked if the authorization fails
 * @param throwAuthError Whether to throw errors on authorization failures (defaults to false)
 * @param config An optional axios request config (use this to provide request data)
 *
 * @returns The axios response
 * @throws `AxiosError` in case of failure
 * @throws `NullTokenError` if the provided token is `null`
 */
export async function sendAuthorizedRequest(
  method: Method,
  url: string,
  token: string,
  onAuthError: () => any,
  throwAuthError: boolean = false,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<any>> {
  if (token === null) {
    onAuthError();
    if (throwAuthError) {
      throw new NullTokenError();
    }
  }

  const extendedConfig: AxiosRequestConfig = {
    ...config,
    method,
    url,
  };

  // Add Authorization header
  if (typeof extendedConfig.headers === "undefined") {
    extendedConfig.headers = {};
  }
  extendedConfig.headers.Authorization = `Bearer ${token}`;

  // Send request
  try {
    return await axios.request(extendedConfig);
  } catch (error) {
    if ((error as AxiosError).response?.status === 401) {
      onAuthError();
      if (throwAuthError) {
        throw error;
      }
      return (error as AxiosError).response;
    } else {
      throw error;
    }
  }
}

/**
 * Sends a GET request using `sendAuthorizedRequest` to the API and returns the results.
 *
 * @param endpoint The API endpoint
 * @param token The auth token
 * @param onAuthError A function that is invoked if the authorization fails
 *
 * @returns The axios response
 * @throws `AxiosError` in case of failure
 */
export async function fetchApiDataAuthorized<E extends ApiDataEndpoint>(
  endpoint: E,
  token: string,
  onAuthError: () => any
): Promise<ApiDataEndpointReturnType<E>> {
  const reply = await sendAuthorizedRequest("GET", getApiUrl(endpoint), token, onAuthError, true);
  return reply.data;
}
