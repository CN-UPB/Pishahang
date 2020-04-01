import { createReducer } from "typesafe-actions";

import { resetInfoDialog, showErrorInfoDialog } from "./../actions/global";
import { resetSnackbar, showSnackbar } from "../actions/global";

export type GlobalState = Readonly<{
  /** Global snackbar */
  snackbar: {
    message: string;
    isVisible: boolean;
  };

  /** Global info dialog  */
  infoDialog: {
    message: string;
    isVisible: boolean;
    type: "" | "error";
  };
}>;

const initialState: GlobalState = {
  snackbar: {
    message: "",
    isVisible: false,
  },
  infoDialog: {
    message: "",
    isVisible: false,
    type: "",
  },
};

const globalReducer = createReducer(initialState)
  .handleAction(showSnackbar, (state, action) => ({
    ...state,
    snackbar: {
      message: action.payload,
      isVisible: true,
    },
  }))
  .handleAction(resetSnackbar, (state, action) => ({
    ...state,
    snackbar: {
      message: "",
      isVisible: false,
    },
  }))

  .handleAction(showErrorInfoDialog, (state, action) => ({
    ...state,
    infoDialog: {
      message: action.payload,
      isVisible: false,
      type: "error",
    },
  }))
  .handleAction(resetInfoDialog, (state, action) => ({
    ...state,
    infoDialog: {
      message: "",
      isVisible: false,
      type: "",
    },
  }));

export default globalReducer;
