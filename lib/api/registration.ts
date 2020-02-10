import axios, { AxiosError, AxiosRequestConfig, AxiosResponse, Method } from "axios";

import { ApiReply } from "./../models/ApiReply";
import { Session } from "./../models/Session";
import { RegisterUser } from "../models/RegisterUser";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "./endpoints";
import { getApiUrl } from "./index";

/**
 * Sends a registration request to the API
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure. In case of
 * success, the resulting `Session` object is provided via the `payload` attribute.
 */
export async function registration(userdata: RegisterUser): Promise<ApiReply> {
  try {
    const reply = await axios.post(getApiUrl("users"), userdata);
    return { success: true };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 401:
        return { success: false, message: "Invalid username or password" };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}
