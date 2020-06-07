import { fork } from "redux-saga/effects";

import { isClient } from "../../util/environment";
import { authSaga } from "./auth";

export function* rootSaga() {
  if (isClient) {
    yield fork(authSaga);
  }
}
