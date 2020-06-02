import axios, { AxiosError } from "axios";

import { ApiReply } from "../models/ApiReply";
import { VimType } from "../models/Vims";
import { getApiUrl } from ".";

/**
 * Uploads Vims data through the API
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure. In case of
 * success, the resulting `Session` object is provided via the `payload` attribute.
 */
export async function uploadVim(vimType: VimType, vimContent: any): Promise<ApiReply> {
  try {
    return {
      success: true,
      payload: await axios.post(getApiUrl("vims"), {
        vim: vimContent,
        type: vimType,
      }),
    };
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
 * Sends a remove/delete request to the API
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure.
 */

export async function removeVim(id: String): Promise<ApiReply> {
  try {
    if (id == null) return;
    let reply = await axios.delete(getApiUrl("vims/" + id));
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
