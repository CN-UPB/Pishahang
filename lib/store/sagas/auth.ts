import { call, fork, put, take, takeLatest } from "redux-saga/effects";
import { getType } from "typesafe-actions";

import * as api from "./../../api/auth";
import { ApiReply } from "./../../models/ApiReply";
import * as actions from "./../actions/auth";

/**
 * Handles the login action
 */
export function* loginSaga(loginAction: ReturnType<typeof actions.login>) {
  const { username, password } = loginAction.payload;
  const reply: ApiReply = yield call(api.login, username, password);
  if (!reply.success) {
    yield put(actions.loginError(reply.message));
  } else {
    yield put(actions.loginSuccess(reply.payload));
  }
}

/**
 * Routes to the login page on every authError action
 */
function* authErrorHandlerSaga() {
  while (true) {
    yield take(getType(actions.authError));
  }
}

export function* authSaga() {
  yield takeLatest(getType(actions.login), loginSaga);
  yield fork(authErrorHandlerSaga);
}
