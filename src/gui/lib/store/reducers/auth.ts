import { createReducer } from "typesafe-actions";

import { User } from "./../../models/User";
import { Tokens } from "../../models/Tokens";
import * as actions from "./../actions/auth";

export type AuthState = Readonly<{
  tokens: Tokens;
  loginErrorMessage: string;
  user: User;
}>;

const initialState: AuthState = {
  tokens: null,
  loginErrorMessage: "",
  user: null,
};

const authReducer = createReducer(initialState)
  .handleAction(actions.loginError, (state, action) => ({
    ...state,
    loginErrorMessage: action.payload,
  }))
  .handleAction(actions.loginSuccess, (state, action) => ({
    ...state,
    tokens: action.payload,
    loginErrorMessage: "",
  }))
  .handleAction(actions.setUser, (state, action) => ({
    ...state,
    user: action.payload,
  }))
  .handleAction(actions.setAccessToken, (state, action) => ({
    ...state,
    tokens: {
      ...state.tokens,
      ...action.payload,
    },
  }))
  .handleAction([actions.logout, actions.authError], (state) => ({
    ...state,
    tokens: null,
    user: null,
  }));

export default authReducer;
