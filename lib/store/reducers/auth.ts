import { createReducer } from "typesafe-actions";

import { Session } from "./../../models/Session";
import * as actions from "./../actions/auth";

export type AuthState = Readonly<{
  session: Session;
  loginErrorMessage: string;
}>;

const initialState: AuthState = {
  session: null,
  loginErrorMessage: null,
};

const authReducer = createReducer(initialState)
  .handleAction(actions.loginError, (state, action) => ({
    ...state,
    loginErrorMessage: action.payload,
  }))
  .handleAction(actions.loginSuccess, (state, action) => ({
    ...state,
    session: action.payload,
    loginErrorMessage: "",
  }))
  .handleAction(actions.logout, (state, action) => ({
    ...state,
    session: null,
  }))
  .handleAction(actions.authError, state => ({
    ...state,
    session: null,
  }));

export default authReducer;
