import { createAction } from "typesafe-actions";

import { Session } from "../../models/Session";

/**
 * Can be dispatched to log in a user, providing its username and password.
 */
export const login = createAction("Auth:Login")<{ username: string; password: string }>();

/**
 * Dispatched on successful login, containing the Session object retrieved from the API.
 */
export const loginSuccess = createAction("Auth:Login:Success")<Session>();

/**
 * Dispatched when a login attempt failed, containing a user-friendly error message.
 */
export const loginError = createAction("Auth:Login:Error")<string>();

/**
 * Can be dispatched to log out the current user.
 */
export const logout = createAction("Auth:Logout")();

/**
 * Dispatched when authentication fails for any api request, except of login requests.
 */
export const authError = createAction("Auth:Error")();
