import { RootState } from "StoreTypes";

export const selectSnackbarMessage = (state: RootState) => state.global.snackbar.message;
export const selectSnackbarIsVisible = (state: RootState) => state.global.snackbar.isVisible;
