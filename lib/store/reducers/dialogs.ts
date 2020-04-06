import { createReducer } from "typesafe-actions";

import {
  resetInfoDialog,
  resetTableDialog,
  showDescriptorInfoDialog,
  showInfoDialog,
  showServiceInfoDialog,
} from "../actions/dialogs";
import { resetSnackbar, showSnackbar } from "../actions/dialogs";

export type GlobalState = Readonly<{
  /** Snackbar */
  snackbar: {
    message: string;
    isVisible: boolean;
  };

  /** Info dialog  */
  infoDialog: {
    title: string;
    message: string;
    isVisible: boolean;
  };

  /** Table dialog  */
  tableDialog: {
    title: string;
    content: [string, string][];
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

  tableDialog: {
    title: "",
    content: [],
    isVisible: false,
  },
};

const globalReducer = createReducer(initialState)
  // Snackbar
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

  // Info dialog
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
  }))

  // Table info dialog
  .handleAction(showDescriptorInfoDialog, (state, action) => ({
    ...state,
    tableDialog: {
      title: "Test",
      content: [["Test", "foo"]],
      isVisible: true,
    },
  }))
  .handleAction(showServiceInfoDialog, (state, action) => ({
    ...state,
    tableDialog: {
      title: "Bar",
      content: [["Bar", "foo"]],
      isVisible: true,
    },
  }))
  .handleAction(resetTableDialog, (state, action) => ({
    ...state,
    tableDialog: {
      title: "",
      content: [],
      isVisible: false,
    },
  }));

export default globalReducer;
