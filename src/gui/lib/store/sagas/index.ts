import { fork } from "redux-saga/effects";

import { authSaga } from "./auth";

export function* rootSaga() {
  yield fork(authSaga);
}
