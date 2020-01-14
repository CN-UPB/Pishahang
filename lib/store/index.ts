import rootReducer from "./reducers";
import { rootSaga } from "./sagas";
import { applyMiddleware, createStore, Store } from "redux";
import createSagaMiddleware from "redux-saga";
import { RootState } from "StoreTypes";
import { MakeStoreOptions } from "next-redux-wrapper";

export const makeStore = (initialState: RootState, { isServer, req }: MakeStoreOptions) => {
  const sagaMiddleware = createSagaMiddleware();
  let store: Store;

  if (isServer) {
    store = createStore(rootReducer, initialState, applyMiddleware(sagaMiddleware));
  } else {
    const { composeWithDevTools } = require("redux-devtools-extension/logOnlyInProduction");
    store = createStore(
      rootReducer,
      initialState,
      composeWithDevTools(applyMiddleware(sagaMiddleware))
    );
  }

  if (req || !isServer) {
    (store as any).sagaTask = sagaMiddleware.run(rootSaga);
  }

  return store;
};
