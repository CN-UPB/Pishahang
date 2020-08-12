import { LocalUser, User } from "./../../models/User";
import { getApiUrl } from "../../api/index";
import { ApiThunkOptions, callApiEnhanced } from "./auth";

/**
 * Return a thunk action that adds a new user via the API
 */
export function addUser(data: LocalUser, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<User>({ method: "POST", url: getApiUrl("users"), data }, apiThunkOptions);
}

/**
 * Return a thunk action that updates an existing user via the API
 */
export function updateUser(userId: string, userData: LocalUser, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<User>(
    { method: "PUT", url: getApiUrl(`users/${userId}`), data: userData },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that deletes a user via the API
 */
export function deleteUser(userId: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<User>(
    { method: "DELETE", url: getApiUrl(`users/${userId}`) },
    apiThunkOptions
  );
}
