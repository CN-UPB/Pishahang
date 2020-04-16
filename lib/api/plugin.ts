/**
 * Fetches a descriptor based on the given ID
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure.
 */

import axios, { AxiosError } from "axios";

import { ApiReply } from "../models/ApiReply";
import { getApiUrl } from ".";

export async function getPlugin(id: String): Promise<ApiReply> {
  try {
    if (id == null) return;
    let reply = await axios.get(getApiUrl("plugins/" + id));
    console.log(reply);
    return { success: true, payload: reply.data };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 401:
        return { success: false, message: "Invalid data" };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}

/**
 * Sends a Stop request to the API
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure.
 */

export async function stopPlugin(id: String): Promise<ApiReply> {
  try {
    if (id == null) return;
    let reply = await axios.delete(getApiUrl("plugins/" + id));
    console.log(reply);
    return { success: true };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 401:
        return { success: false, message: "Invalid data" };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}

/**
 * Updates a Plugin with the given id
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure.
 */

export async function changePluginLifecycleState(
  id: String,
  state: "pause" | "start"
): Promise<ApiReply> {
  try {
    await axios.put(getApiUrl("plugins/" + id + "/lifecycle"), { targetState: state });
    return { success: true };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 401:
        return { success: false, message: "Invalid data" };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}
