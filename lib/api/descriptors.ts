import axios, { AxiosError } from "axios";

import { Descriptor } from "./../models/Descriptor";
import { ApiReply } from "../models/ApiReply";
import { DescriptorContent } from "../models/Descriptor";
import { DescriptorType } from "../models/Descriptor";
import { getApiUrl } from "./index";

/**
 * Sends a registration request to the API
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure. In case of
 * success, the resulting `Descriptor` object is provided via the `payload` attribute.
 */
export async function uploadDescriptor(
  type: DescriptorType,
  content: any
): Promise<ApiReply<Descriptor>> {
  try {
    const reply = await axios.post(getApiUrl("descriptors"), { content, type });
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
 * Fetches a descriptor based on the given UUID
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure.
 */

export async function getDescriptor(uuid: String): Promise<ApiReply> {
  try {
    if (uuid == null) return;
    const reply = await axios.get(getApiUrl("descriptors/" + uuid));
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
 * Sends a deletion request to the API
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure.
 */

export async function deleteDescriptor(uuid: String): Promise<ApiReply> {
  try {
    if (uuid == null) return;
    await axios.delete(getApiUrl("descriptors/" + uuid));
    console.log(uuid);

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
 * Updates a descriptor with the given uuid
 *
 *
 *
 * @returns An `ApiReply` object with a user-friendly error message in case of failure.
 */

export async function updateDescriptor(
  content: DescriptorContent,
  uuid: String
): Promise<ApiReply> {
  try {
    await axios.put(getApiUrl("descriptors/" + uuid), { content });
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
