import { AxiosError, AxiosRequestConfig } from "axios";
import axios from "axios";
import { AppThunkAction } from "StoreTypes";

import { ApiReply } from "./../../models/ApiReply";
import { getApiUrl } from "../../api";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "../../api/endpoints";
import { authError, loginError, loginSuccess } from "./../actions/auth";
import { showSnackbar } from "./../actions/dialogs";
import { selectAccessToken } from "./../selectors/auth";

/**
 * Returns a Redux Thunk that performs an HTTP request using axios and sets an
 * `Authorization` header with the token selected from the store and returns the reply
 * data as an object. An `authError` action is dispatched and `null` is returned in case
 * of an authorization failure (when the server replies with status code 401) or if the
 * token is `null`.
 *
 * @param config The axios request config object
 */
export function callApiAuthorized<ReplyDataType = any>(
  config: AxiosRequestConfig
): AppThunkAction<Promise<ReplyDataType>> {
  return async (dispatch, getState) => {
    const token = selectAccessToken(getState());

    if (token === null) {
      dispatch(authError());
      return null;
    }

    // Add Authorization header
    if (typeof config.headers === "undefined") {
      config.headers = {};
    }
    config.headers.Authorization = `Bearer ${token}`;

    // Send request
    try {
      return (await axios.request<ReplyDataType>(config)).data;
    } catch (error) {
      if ((error as AxiosError).response?.status === 401) {
        dispatch(authError());
        return null;
      }
      throw error;
    }
  };
}

/**
 * Returns a Thunk action creator that sends an authorized GET request to the API and
 * returns the results.
 *
 * @param endpoint The API endpoint
 */
export function fetchApiDataAuthorized<E extends ApiDataEndpoint>(endpoint: E) {
  return callApiAuthorized<ApiDataEndpointReturnType<E>>({
    method: "GET",
    url: getApiUrl(endpoint),
  });
}

export type ApiThunkOptions = {
  /**
   * If an error is encountered during the API call, show an error info dialog by
   * dispatching a corresponding `showInfoDialog` action (defaults to `true`). Note that
   * error dialogs are not shown on authentication errors; `callApiAuthorized`
   * dispatches an `authError` instead.
   */
  showErrorInfoDialog?: boolean;
  /**
   * If set, a snackbar with the provided message will be displayed on a success
   * response from the API by dispatching a corresponding `showSnackbar` action
   */
  successSnackbarMessage?: string;
};

/**
 * A wrapper around `callApiAuthorized` that creates a thunk which wraps the reply in an
 * `ApiResponse` object and offers additional convenience functionalities that can be
 * specified by providing an `ApiThunkOptions` object. Note that the thunk may also
 * return `null` if case an authentication error ocurred.
 */
export function callApiEnhanced<ReplyDataType = any>(
  config: AxiosRequestConfig,
  options: ApiThunkOptions = {}
): AppThunkAction<Promise<ApiReply<ReplyDataType>>> {
  options = {
    showErrorInfoDialog: true,
    successSnackbarMessage: null,
    ...options,
  };

  return async (dispatch) => {
    let reply: ApiReply<ReplyDataType>;
    try {
      const replyData = await dispatch(callApiAuthorized<ReplyDataType>(config));
      if (replyData === null) {
        reply = ApiReply.makeError("Unauthenticated");
      } else {
        reply = ApiReply.makeSuccess(replyData);
      }
    } catch (error) {
      reply = ApiReply.fromAxiosError(error);
      if (options.showErrorInfoDialog) {
        dispatch(reply.toErrorDialogAction());
      }
    }

    if (reply.success && options.successSnackbarMessage !== null) {
      dispatch(showSnackbar(options.successSnackbarMessage));
    }

    return reply;
  };
}

/**
 * Return a thunk that sends a login request to the API. Dispatches either a
 * `loginSuccess` or a `loginError` action.
 *
 * @param username The username to be submitted
 * @param password The password to be submitted
 */
export function login(username: string, password: string): AppThunkAction {
  return async (dispatch) => {
    try {
      const replyData = (await axios.post(getApiUrl("auth"), { username, password })).data;
      const now = Math.round(Date.now() / 1000);
      dispatch(
        loginSuccess({
          accessToken: replyData.accessToken,
          refreshToken: replyData.refreshToken,
          accessTokenExpiresAt: now + replyData.accessTokenExpiresIn,
          refreshTokenExpiresAt: now + replyData.refreshTokenExpiresIn,
        })
      );
    } catch (error) {
      let message: string;
      if ((error as AxiosError).response?.status === 401) {
        message = "Invalid username or password";
      } else {
        message = "An unexpected error ocurred. Please try again.";
      }
      dispatch(loginError(message));
    }
  };
}
