import { createReducer } from "typesafe-actions";

export type UserState = Readonly<{}>;

const initialState: UserState = {};

const userReducer = createReducer(initialState);

export default userReducer;
