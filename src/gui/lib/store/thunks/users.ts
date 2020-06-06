import { User } from "./../../models/User";
import { getApiUrl } from "../../api/index";
import { UserData } from "../../models/UserData";
import { ApiThunkOptions, callApiEnhanced } from "./auth";

/**
 * Return a thunk action that adds a new user via the API
 */
export function addUser(data: UserData, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<User>({ method: "POST", url: getApiUrl("users"), data }, apiThunkOptions);
}
