// Redux-store-related type definitions
declare module "StoreTypes" {
  import { StateType, ActionType } from "typesafe-actions";
  import { Store as ReduxStore } from "redux";
  export type RootAction = ActionType<typeof import("./actions").default>;
  export type RootState = StateType<typeof import("./reducers").default>;
  export type Store = ReduxStore<RootState, RootAction>;
}
