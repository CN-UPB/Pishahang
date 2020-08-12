import { RootAction } from "StoreTypes";

// Make createReducer typesafe without explicit type parameters
declare module "typesafe-actions" {
  interface Types {
    RootAction: RootAction;
  }
}
