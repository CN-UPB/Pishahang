import Router from "next/router";
import { call, fork, takeEvery } from "redux-saga/effects";
import { getType } from "typesafe-actions";

import { loginSuccess } from "./../actions/auth";
import { authError, logout } from "../actions/auth";

export function* redirectSaga(targetPath: string) {
  yield call(Router.push, targetPath);
}

/**
 * Redirects the client to the dashboard on every `loginSuccess` action and to the login
 * page on every `logout` or `authError` action.
 */
export function* authSaga() {
  yield takeEvery(getType(loginSuccess), redirectSaga, "/");
  yield takeEvery([getType(logout), getType(authError)], redirectSaga, "/login");
}
