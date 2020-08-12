// Redux-store-related type definitions
declare module "StoreTypes" {
  import { StateType, ActionType } from "typesafe-actions";
  import { Store as ReduxStore, Action } from "redux";
  import { ThunkAction, ThunkDispatch } from "redux-thunk";

  export type RootAction = ActionType<typeof import("./actions").default>;
  export type RootState = StateType<typeof import("./reducers").default>;
  export type Store = ReduxStore<RootState, RootAction>;

  // Using `interface` instead of `type` to improve type hint readability:
  export interface AppThunkAction<ReturnType = void>
    extends ThunkAction<ReturnType, RootState, unknown, RootAction> {}
  export type AppThunkDispatch = ThunkDispatch<RootState, unknown, RootAction>;
}
