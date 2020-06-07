import Router from "next/router";
import { expectSaga } from "redux-saga-test-plan";

import { Tokens } from "../../models/Tokens";
import { loginSuccess, logout } from "./../actions/auth";
import { authError } from "../actions/auth";
import { authSaga } from "./auth";

// Mock Next.js router – it throws an error if imported in an environment other than client-side Next.js
jest.mock("next/router");

expectSaga.DEFAULT_TIMEOUT = 100;

const tokens: Tokens = {
  accessToken: "token",
  accessTokenExpiresAt: 0,
  refreshToken: "refresh token",
  refreshTokenExpiresAt: 0,
};

describe("authSaga", () => {
  it('should redirect to "/" on successful login', () => {
    return expectSaga(authSaga).dispatch(loginSuccess(tokens)).call(Router.push, "/").silentRun();
  });

  it('should redirect to "/login" on logout or authentication errors', async () => {
    await expectSaga(authSaga).dispatch(logout()).call(Router.push, "/login").silentRun();
    await expectSaga(authSaga).dispatch(authError()).call(Router.push, "/login").silentRun();
  });
});
