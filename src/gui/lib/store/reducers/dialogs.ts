import { createReducer } from "typesafe-actions";

import { Descriptor } from "./../../models/Descriptor";
import { ApiDataEndpoint } from "../../api/endpoints";
import { VimType } from "../../models/Vim";
import { formatDate } from "../../util/time";
import {
  resetDescriptorEditorDialog,
  setDescriptorEditorDialogContentString,
  showDescriptorEditorDialog,
} from "./../actions/dialogs";
import {
  resetInfoDialog,
  resetTableDialog,
  showDescriptorInfoDialog,
  showInfoDialog,
  showPluginInfoDialog,
  showServiceInfoDialog,
  showVimInfoDialog,
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

  /** Descriptor editor dialog */
  descriptorEditorDialog: {
    isVisible: boolean;
    descriptor: Descriptor;

    /** The endpoint from which the descriptor was fetched (will be used to trigger SWR revalidation) */
    endpoint: ApiDataEndpoint;

    /** The current content text (may differ from the descriptor text) */
    currentContentString: string;
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

  descriptorEditorDialog: {
    isVisible: false,
    descriptor: null,
    endpoint: null,
    currentContentString: "",
  },
};

const reducer = createReducer(initialState)
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
      // Leaving the title and message in place so they do not disappear prior to dialog fadeout
      ...state.infoDialog,
      isVisible: false,
    },
  }))

  // Table info dialog
  .handleAction(showDescriptorInfoDialog, (state, { payload: descriptor }) => ({
    ...state,
    tableDialog: {
      title: descriptor.content.name,
      content: [
        ["Name", descriptor.content.name],
        ["Vendor", descriptor.content.vendor],
        ["Version", descriptor.content.version],
        ["Description", descriptor.content.description],
        ["Created at", formatDate(descriptor.createdAt)],
        ["Updated at", formatDate(descriptor.updatedAt)],
        ["ID", descriptor.id],
      ],
      isVisible: true,
    },
  }))
  .handleAction(showServiceInfoDialog, (state, { payload: service }) => ({
    ...state,
    tableDialog: {
      title: service.name,
      content: [
        ["Name", service.name],
        ["Vendor", service.vendor],
        ["Version", service.version],
        ["Onboarded at", formatDate(service.createdAt)],
        ["ID", service.id],
      ],
      isVisible: true,
    },
  }))
  .handleAction(showPluginInfoDialog, (state, { payload: plugin }) => ({
    ...state,
    tableDialog: {
      title: plugin.name,
      content: [
        ["Description", plugin.description],
        ["LastHeartbeatAt", formatDate(plugin.lastHeartbeatAt)],
        ["RegisteredAt", formatDate(plugin.registeredAt)],
        ["UUID", plugin.id],
      ],
      isVisible: true,
    },
  }))
  .handleAction(showVimInfoDialog, (state, { payload: vim }) => ({
    ...state,
    tableDialog: {
      title: vim.name,
      content: [
        ["Name", vim.name],
        ["Id", vim.id],
        ["Country", vim.country],
        ["City", vim.city],
        ["Type", vim.type],
        ...((vim.type == VimType.Aws
          ? []
          : !vim.resourceUtilization
          ? ["Resource utilization", "Currently not available"]
          : [
              ["Cores total", vim.resourceUtilization.cores.total.toString()],
              ["Cores used", vim.resourceUtilization.cores.used.toString()],
              ["Memory total", vim.resourceUtilization.memory.total.toString()],
              ["Memory used", vim.resourceUtilization.memory.used.toString()],
            ]) as [string, string][]),
      ],
      isVisible: true,
    },
  }))
  .handleAction(resetTableDialog, (state, action) => ({
    ...state,
    tableDialog: {
      // Leaving the title and content in place so they do not disappear prior to dialog fadeout
      ...state.tableDialog,
      isVisible: false,
    },
  }))

  // Descriptor editor dialog
  .handleAction(showDescriptorEditorDialog, (state, { payload: { descriptor, endpoint } }) => ({
    ...state,
    descriptorEditorDialog: {
      isVisible: true,
      descriptor,
      endpoint,
      currentContentString: descriptor.contentString,
    },
  }))
  .handleAction(setDescriptorEditorDialogContentString, (state, { payload: contentString }) => ({
    ...state,
    descriptorEditorDialog: {
      ...state.descriptorEditorDialog,
      currentContentString: contentString,
    },
  }))
  .handleAction(resetDescriptorEditorDialog, (state, action) => ({
    ...state,
    descriptorEditorDialog: {
      descriptor: null,
      endpoint: null,
      currentContentString: state.descriptorEditorDialog.currentContentString, // To avoid content flashes
      isVisible: false,
    },
  }));

export default reducer;
