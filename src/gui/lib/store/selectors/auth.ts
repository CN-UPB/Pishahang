import { createSelector } from "reselect";
import { RootState } from "StoreTypes";

export const selectIsLoggedIn = (state: RootState) => selectTokens(state) !== null;
export const selectLoginErrorMessage = (state: RootState) => state.auth.loginErrorMessage;

export const selectTokens = (state: RootState) => state.auth.tokens;
export const selectAccessToken = createSelector([selectTokens], (tokens) => tokens?.accessToken);
export const selectRefreshToken = createSelector([selectTokens], (tokens) => tokens?.refreshToken);

export const selectUser = (state: RootState) => state.auth.user;
export const selectUserIsAdmin = createSelector([selectUser], (user) => user?.isAdmin);
export const selectUserFullName = createSelector([selectUser], (user) => user?.fullName);
export const selectUserEmail = createSelector([selectUser], (user) => user?.email);
export const selectUserId = createSelector([selectUser], (user) => user?.id);
export const selectUserCreatedAt = createSelector([selectUser], (user) => user?.createdAt);
export const selectUserUpdatedAt = createSelector([selectUser], (user) => user?.updatedAt);
