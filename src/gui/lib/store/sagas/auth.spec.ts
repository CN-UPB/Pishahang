import Router from "next/router";
import { expectSaga } from "redux-saga-test-plan";
import { call } from "redux-saga/effects";

import * as api from "../../api/auth";
import { Tokens } from "../../models/Tokens";
import * as actions from "./../actions/auth";
import { loginSaga } from "./auth";

// Mock Next.js router – it throws an error if imported in an environment other than client-side Next.js
jest.mock("next/router");

describe("loginSaga", () => {
  const tokens: Tokens = {
    accessToken: "token",
    accessTokenExpiresAt: 0,
    refreshToken: "refresh token",
    refreshTokenExpiresAt: 0,
  };

  it("should dispatch loginSuccess and redirect on successful login", () => {
    return expectSaga(loginSaga, actions.login({ username: "user", password: "pass" }))
      .provide([[call(api.login, "user", "pass"), { success: true, payload: tokens }]])
      .put(actions.loginSuccess(tokens))
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
