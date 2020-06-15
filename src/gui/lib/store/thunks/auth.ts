import { AxiosError, AxiosRequestConfig } from "axios";
import axios from "axios";
import { AppThunkAction } from "StoreTypes";

import { ApiReply } from "./../../models/ApiReply";
import { User } from "./../../models/User";
import { getTimestamp } from "./../../util/time";
import { getApiUrl } from "../../api";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "../../api/endpoints";
import { authError, loginError, loginSuccess, setAccessToken, setUser } from "./../actions/auth";
import { showSnackbar } from "./../actions/dialogs";
import { selectAccessToken, selectRefreshToken } from "./../selectors/auth";

/**
 * Returns a Redux Thunk that performs an HTTP request using axios and sets an
 * `Authorization` header with the token selected from the store and returns the reply
 * data as an object.
 *
 * If the token in the store is `null`, `null` is returned and an `authError` action is
 * dispatched.
 *
 * If he server replies with status code 401, the `refreshAccessToken` thunk is executed. The
 * request is repeated if it succeeds, and `authError` is dispatched otherwise.
 *
 * @param config The axios request config object
 */
export function callApiAuthorized<ReplyDataType = any>(
  config: AxiosRequestConfig
): AppThunkAction<Promise<ReplyDataType>> {
  return async (dispatch, getState) => {
    if (typeof config.headers === "undefined") {
      config.headers = {};
    }

    let retried = false;
    while (true) {
      const token = selectAccessToken(getState());

      if (token === null) {
        break; // Dispatch auth error and return null
      }

      // Set Authorization header
      config.headers.Authorization = `Bearer ${token}`;

      try {
        return (await axios.request<ReplyDataType>(config)).data;
      } catch (error) {
        if ((error as AxiosError).response?.status !== 401) {
          throw error;
        }

        // Token seems to be invalid, optionally trying to refresh it
        if (!retried && (await dispatch(refreshAccessToken()))) {
          retried = true;
        } else {
          break; // Dispatch auth error and return null
        }
      }
    }

    dispatch(authError());
    return null;
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
      const now = getTimestamp();
      dispatch(
        loginSuccess({
          accessToken: replyData.accessToken,
          refreshToken: replyData.refreshToken,
          accessTokenExpiresAt: now + replyData.accessTokenExpiresIn,
          refreshTokenExpiresAt: now + replyData.refreshTokenExpiresIn,
        })
      );
      dispatch(fetchUser());
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

/**
 * Return a thunk that fetches the currently logged-in user and dispatches a `setUser`
 * action on success, or `authError` otherwise.
 */
export function fetchUser(): AppThunkAction {
  return async (dispatch) => {
    try {
      const user = await dispatch(
        callApiAuthorized<User>({
          method: "GET",
          url: getApiUrl("current-user"),
        })
      );
      if (user !== null) {
        // null is returned on an auth error
        dispatch(setUser(user));
      }
    } catch {
      // This might be an error 500 or a connection problem
      dispatch(authError());
    }
  };
}

/**
 * Return a thunk that refreshes the access token using the refresh token and dispatches
 * `setAccessToken` on success, or `authError` on error.
 */
export function refreshAccessToken(): AppThunkAction<Promise<Boolean>> {
  return async (dispatch, getState) => {
    try {
      const replyData = (
        await axios.put(getApiUrl("auth"), { refreshToken: selectRefreshToken(getState()) })
      ).data;
      dispatch(
        setAccessToken({
          accessToken: replyData.accessToken,
          accessTokenExpiresAt: getTimestamp() + replyData.accessTokenExpiresIn,
        })
      );
      return true;
    } catch (error) {
      dispatch(authError());
      return false;
    }
  };
}
