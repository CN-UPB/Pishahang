import { createAction } from "typesafe-actions";

import { AccessToken, Tokens } from "./../../models/Tokens";
import { User } from "./../../models/User";

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
 * Can be dispatched to log the current user out. Resets the stored auth and user data.
 */
export const logout = createAction("Auth:Logout")();

/**
 * Can be dispatched when API authentication fails for a request. Resets the stored auth
 * and user data.
 */
export const authError = createAction("Auth:Error")();

/**
 * Set the access token and its expiry date
 */
export const setAccessToken = createAction("Auth:Tokens:setAccess")<AccessToken>();

/**
 * Set the user data of the currently logged-in user
 */
export const setUser = createAction("Auth:User:set")<User>();
