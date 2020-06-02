import { RootState } from "StoreTypes";

export const selectSnackbarMessage = (state: RootState) => state.dialogs.snackbar.message;
export const selectSnackbarIsVisible = (state: RootState) => state.dialogs.snackbar.isVisible;

export const selectInfoDialogTitle = (state: RootState) => state.dialogs.infoDialog.title;
export const selectInfoDialogMessage = (state: RootState) => state.dialogs.infoDialog.message;
export const selectInfoDialogIsVisible = (state: RootState) => state.dialogs.infoDialog.isVisible;

export const selectTableDialogTitle = (state: RootState) => state.dialogs.tableDialog.title;
export const selectTableDialogContent = (state: RootState) => state.dialogs.tableDialog.content;
export const selectTableDialogIsVisible = (state: RootState) => state.dialogs.tableDialog.isVisible;
