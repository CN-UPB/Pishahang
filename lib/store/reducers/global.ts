import { resetSnackbar, showSnackbar } from "../actions/global";
import { createReducer } from "typesafe-actions";

export type GlobalState = Readonly<{
  /**
   * Information related to the global snackbar
   */
  snackbar: {
    message: string;
    visible: boolean;
  };
}>;

const initialState: GlobalState = {
  snackbar: {
    message: "",
    visible: false,
  },
};

const globalReducer = createReducer(initialState)
  .handleAction(showSnackbar, (state, action) => ({
    ...state,
    snackbar: {
      message: action.payload,
      visible: true,
    },
  }))
  .handleAction(resetSnackbar, (state, action) => ({
    ...state,
    snackbar: {
      message: "",
      visible: false,
    },
  }));

export default globalReducer;
