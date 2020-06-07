import { NewUser, User } from "./../../models/User";
import { getApiUrl } from "../../api/index";
import { ApiThunkOptions, callApiEnhanced } from "./auth";

/**
 * Return a thunk action that adds a new user via the API
 */
export function addUser(data: NewUser, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<User>({ method: "POST", url: getApiUrl("users"), data }, apiThunkOptions);
}
