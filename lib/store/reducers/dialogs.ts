import { createReducer } from "typesafe-actions";

import { resetInfoDialog, showInfoDialog } from "../actions/dialogs";
import { resetSnackbar, showSnackbar } from "../actions/dialogs";

export type GlobalState = Readonly<{
  /** Global snackbar */
  snackbar: {
    message: string;
    isVisible: boolean;
  };

  /** Global info dialog  */
  infoDialog: {
    title: string;
    message: string;
    isVisible: boolean;
  };
}>;

const initialState: GlobalState = {
  snackbar: {
    message: "",
    isVisible: false,
  },

  infoDialog: {
    title: "",
    message: "",
    isVisible: false,
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

  .handleAction(showInfoDialog, (state, action) => ({
    ...state,
    infoDialog: {
      title: action.payload.title,
      message: action.payload.message,
      isVisible: true,
    },
  }))
  .handleAction(resetInfoDialog, (state, action) => ({
    ...state,
    infoDialog: {
      title: "",
      message: "",
      isVisible: false,
    },
  }));

export default globalReducer;
