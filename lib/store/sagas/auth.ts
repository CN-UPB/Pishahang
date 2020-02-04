import Router from "next/router";
import { call, fork, put, take, takeLatest } from "redux-saga/effects";
import { getType } from "typesafe-actions";

import * as api from "./../../api/auth";
import { ApiReply } from "./../../models/ApiReply";
import { isClient } from "./../../util/environment";
import * as actions from "./../actions/auth";

/**
 * Handles the login action (should only be executed on the client side)
 */
export function* loginSaga(loginAction: ReturnType<typeof actions.login>) {
  const { username, password } = loginAction.payload;
  const reply: ApiReply = yield call(api.login, username, password);
  if (!reply.success) {
    yield put(actions.loginError(reply.message));
  } else {
    yield put(actions.loginSuccess(reply.payload));
    yield call(Router.push, "/");
  }
}

/**
 * Handles the login action (should only be executed on the client side)
 */
export function* logoutSaga() {
  yield call(Router.push, "/login");
}

/**
 * Routes to the login page on every authError action (should only be executed on the client side)
 */
function* authErrorHandlerSaga() {
  while (true) {
    yield take(getType(actions.authError));
    if (isClient) {
      yield call(Router.push, "/login");
    }
  }
}

export function* authSaga() {
  if (isClient) {
    yield takeLatest(getType(actions.login), loginSaga);
    yield takeLatest(getType(actions.logout), logoutSaga);
    yield fork(authErrorHandlerSaga);
  }
}
