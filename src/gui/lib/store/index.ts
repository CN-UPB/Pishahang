import { MakeStoreOptions } from "next-redux-wrapper";
import { useDispatch } from "react-redux";
import { Store, applyMiddleware, createStore } from "redux";
import createSagaMiddleware from "redux-saga";
import thunk from "redux-thunk";
import { AppThunkDispatch, RootState } from "StoreTypes";

import rootReducer from "./reducers";
import { rootSaga } from "./sagas";

export const makeStore = (initialState: RootState, { isServer, req }: MakeStoreOptions) => {
  const sagaMiddleware = createSagaMiddleware();
  const enhancer = applyMiddleware(thunk, sagaMiddleware);
  let store: Store;
  if (isServer) {
    store = createStore(rootReducer, initialState, enhancer);
  } else {
    const { composeWithDevTools } = require("redux-devtools-extension/logOnlyInProduction");
    store = createStore(rootReducer, initialState, composeWithDevTools(enhancer));
  }

  if (!isServer) {
    sagaMiddleware.run(rootSaga);
  }

  return store;
};

export const useThunkDispatch = () => useDispatch<AppThunkDispatch>();
