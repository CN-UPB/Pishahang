import Router from "next/router";
import { expectSaga } from "redux-saga-test-plan";
import { call } from "redux-saga/effects";

import { Session } from "./../../models/Session";
import * as api from "../../api/auth";
import * as actions from "./../actions/auth";
import { loginSaga } from "./auth";

// Mock Next.js router – it throws an error if imported in an environment other than client-side Next.js
jest.mock("next/router");

describe("loginSaga", () => {
  const session: Session = {
    session_began_at: new Date(),
    username: "theUser",
    token: {
      access_token: "token",
      expires_in: 100,
      refresh_expires_in: 100,
      refresh_token: "refresh token",
      session_state: "session state",
      token_type: "token type",
    },
  };

  it("should dispatch loginSuccess and redirect on successful login", () => {
    return expectSaga(loginSaga, actions.login({ username: "user", password: "pass" }))
      .provide([[call(api.login, "user", "pass"), { success: true, payload: session }]])
      .put(actions.loginSuccess(session))
      .call(Router.push, "/")
      .run();
  });

  it("should dispatch loginError on login errors", () => {
    return expectSaga(loginSaga, actions.login({ username: "user", password: "pass" }))
      .provide([[call(api.login, "user", "pass"), { success: false, message: "error message" }]])
      .put(actions.loginError("error message"))
      .run();
  });
});
