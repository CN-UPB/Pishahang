import { RootState } from "StoreTypes";

export const selectSnackbarMessage = (state: RootState) => state.dialogs.snackbar.message;
export const selectSnackbarIsVisible = (state: RootState) => state.dialogs.snackbar.isVisible;

export const selectInfoDialogMessage = (state: RootState) => state.dialogs.infoDialog.message;
export const selectInfoDialogTitle = (state: RootState) => state.dialogs.infoDialog.title;
export const selectInfoDialogIsVisible = (state: RootState) => state.dialogs.infoDialog.isVisible;
