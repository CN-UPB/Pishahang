import axios, { AxiosError, AxiosRequestConfig, AxiosResponse, Method } from "axios";

import { ApiReply } from "../models/ApiReply";
import { Descriptor } from "../models/Descriptor";
import { DescriptorType } from "../models/DescriptorType";
import { RegisterUser } from "../models/RegisterUser";
import { Session } from "../models/Session";
import { VimType } from "../models/Vims";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "./endpoints";
import { getApiUrl } from "./index";

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
    const reply = await axios.post(getApiUrl("vims"), {
      vim: vimContent,
      type: vimType,
    });
    window.location.reload(false);
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
