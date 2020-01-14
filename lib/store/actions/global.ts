import { createAction } from "typesafe-actions";

export const showSnackbar = createAction("Global:Snackbar:show")<string>();
export const resetSnackbar = createAction("Global:Snackbar:reset")();
