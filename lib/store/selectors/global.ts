import { RootState } from "StoreTypes";

export const selectSnackbarMessage = (state: RootState) => state.global.snackbar.message;
export const selectSnackbarVisible = (state: RootState) => state.global.snackbar.visible;
