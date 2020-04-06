import { createAction } from "typesafe-actions";

export const showSnackbar = createAction("Global:Snackbar:show")<string>();
export const resetSnackbar = createAction("Global:Snackbar:reset")();

export const showInfoDialog = createAction("Global:InfoDialog:show")<{
  title: string;
  message: string;
}>();
export const resetInfoDialog = createAction("Global:InfoDialog:reset")();
