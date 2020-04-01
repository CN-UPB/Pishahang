import { createAction } from "typesafe-actions";

export const showSnackbar = createAction("Global:Snackbar:show")<string>();
export const resetSnackbar = createAction("Global:Snackbar:reset")();

export const showErrorInfoDialog = createAction("Global:ErrorInformationDialog:show")<string>();
export const resetInfoDialog = createAction("Global:ErrorInformationDialog:reset")();
