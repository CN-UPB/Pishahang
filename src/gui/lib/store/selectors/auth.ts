import { createSelector } from "reselect";
import { RootState } from "StoreTypes";

export const selectTokens = (state: RootState) => state.auth.tokens;
export const selectIsLoggedIn = (state: RootState) => selectTokens(state) !== null;
export const selectLoginErrorMessage = (state: RootState) => state.auth.loginErrorMessage;

export const selectAccessToken = createSelector([selectTokens], tokens => tokens?.accessToken);
export const selectRefreshToken = createSelector([selectTokens], tokens => tokens?.accessToken);
