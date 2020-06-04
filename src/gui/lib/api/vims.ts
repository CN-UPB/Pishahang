import axios, { AxiosError } from "axios";

import { ApiReply } from "../models/ApiReply";
import { NewVim } from "../models/Vim";
import { getApiUrl } from ".";

export async function addVim(vim: NewVim): Promise<ApiReply> {
  try {
    return {
      success: true,
      payload: await axios.post(getApiUrl("vims"), vim),
    };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 400:
        return { success: false, message: error.response.data.detail };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}

export async function deleteVim(id: string): Promise<ApiReply> {
  try {
    await axios.delete(getApiUrl("vims/" + id));
    return { success: true };
  } catch (error) {
    switch ((error as AxiosError).response?.status) {
      case 400:
        return { success: false, message: error.response.data.details };
      default:
        return { success: false, message: "An unexpected error occurred. Please try again." };
    }
  }
}
