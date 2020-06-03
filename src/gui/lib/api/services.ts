import axios, { AxiosError } from "axios";

import { Service } from "./../models/Service";
import { ApiReply } from "../models/ApiReply";
import { getApiUrl } from "./index";

/**
 * Sends an onboard request to the API
 *
 * @param id The id of the service descriptor to be onboarded
 */
export async function onboardServiceDescriptor(id: string): Promise<ApiReply<Service>> {
  try {
    const reply = await axios.post(getApiUrl("services"), { id });
    return { success: true, payload: reply.data };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 400:
        return {
          success: false,
          message: error.response.data.detail,
        };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}

/**
 * Instantiate a service
 *
 * @param id The id of the service to be instantiated
 */
export async function instantiateService(id: string): Promise<ApiReply<Service>> {
  try {
    const reply = await axios.post(getApiUrl(`services/${id}/instances`));
    return { success: true, payload: reply.data };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 400:
      case 500:
        return {
          success: false,
          message: error.response.data.detail,
        };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}
