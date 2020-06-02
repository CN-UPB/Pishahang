import axios, { AxiosError } from "axios";

import { ApiReply } from "../models/ApiReply";
import { UserData } from "../models/UserData";
import { getApiUrl } from "./index";

/**
 * Sends a user registration request to the API.
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure. In case of
 * success, the resulting `User` object is provided via the `payload` attribute.
 */
export async function registerUser(userData: UserData): Promise<ApiReply> {
  try {
    return {
      success: true,
      payload: await axios.post(getApiUrl("users"), userData),
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
