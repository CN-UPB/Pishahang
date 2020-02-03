import { createSelector } from "reselect";
import { RootState } from "StoreTypes";

export const selectSession = (state: RootState) => state.auth.session;
export const selectIsLoggedIn = (state: RootState) => selectSession(state) !== null;

export const selectAuthToken = createSelector([selectSession], session => {
  if (session) {
    return session.token.access_token;
  }
});
