import { AxiosError } from "axios";

import { showInfoDialog } from "../store/actions/dialogs";

/**
 * An `ApiReply` can be used to represent a reply from the API that can either have a
 * payload, or an error object containing a title and a message property. This way, the
 * return type is uniform, regardless of the API call's outcome.
 *
 * The convenience methods `makeSuccessReply()` and `makeErrorReply()` can be used for
 * instantiation.
 */
export class ApiReply<P = any> {
  constructor(
    readonly payload?: P,
    readonly error?: { title: string; message: string; status?: number }
  ) {}

  /**
   * Return a new `ApiReply` object with the provided payload.
   *
   * @param payload The payload for the returned `ApiReply` object
   */
  static makeSuccess<P = any>(payload?: P) {
    return new ApiReply(payload, null);
  }

  /**
   * Return a new `ApiReply` object that represents an error
   *
   * @param message The error message
   * @param title An optional error title
   */
  static makeError(message: string, title: string = "Error", status?: number) {
    return new ApiReply(null, { message, title, status });
  }

  /**
   * Given an `AxiosError` object that resulted from a gatekeeper API call, returns a
   * corresponding `ApiResponse` object.
   *
   * @param error An `AxiosError` object that resulted from a gatekeeper API call
   */
  static fromAxiosError(error: AxiosError) {
    if (typeof error.response === "undefined") {
      return ApiReply.makeError(
        "An unexpected error occurred. Please try again.",
        "Connection Error"
      );
    }
    const response = (error as AxiosError<{ title: string; detail: string }>).response;
    const data = response.data;
    if (data.title === "") {
      data.title = "Error";
    }
    return ApiReply.makeError(data.detail, data.title, response.status);
  }

  /**
   * If `this.success` is `false`, returns a Redux `showInfoDialog` action that can be
   * dispatched to show a dialog with the error title and message.
   */
  toErrorDialogAction() {
    if (!this.success) {
      return showInfoDialog(this.error);
    }
  }

  /**
   * Whether or not the reply has `error` set to `null`
   */
  get success(): boolean {
    return this.error === null;
  }
}
