import { createAction } from "typesafe-actions";

import { Tokens } from "../../models/Tokens";

/**
 * Can be dispatched to log in a user, providing its username and password.
 */
export const login = createAction("Auth:Login")<{ username: string; password: string }>();

/**
 * Dispatched on successful login, containing the Tokens object with the JWT tokens retrieved from
 * the API.
 */
export const loginSuccess = createAction("Auth:Login:Success")<Tokens>();

/**
 * Dispatched when a login attempt failed, containing a user-friendly error message.
 */
export const loginError = createAction("Auth:Login:Error")<string>();

/**
 * Can be dispatched to log the current user out.
 */
export const logout = createAction("Auth:Logout")();

/**
 * Can be dispatched when API authentication fails for a request. Resets the stored auth data.
 */
export const authError = createAction("Auth:Error")();
