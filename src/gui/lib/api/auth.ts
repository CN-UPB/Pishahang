import axios, { AxiosError } from "axios";

import { ApiReply } from "./../models/ApiReply";
import { Tokens } from "../models/Tokens";
import { getApiUrl } from "./index";

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
    return ApiReply.makeSuccess({
      accessToken: replyData.accessToken,
      refreshToken: replyData.refreshToken,
      accessTokenExpiresAt: now + replyData.accessTokenExpiresIn,
      refreshTokenExpiresAt: now + replyData.refreshTokenExpiresIn,
    });
  } catch (error) {
    if ((error as AxiosError).response?.status === 401) {
      return ApiReply.makeError("Invalid username or password", "Authentication Error");
    }
    return ApiReply.fromAxiosError(error);
  }
}
