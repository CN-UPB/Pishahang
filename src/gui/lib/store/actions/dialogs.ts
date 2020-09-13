import { createAction } from "typesafe-actions";

import { ApiDataEndpoint } from "../../api/endpoints";
import { Descriptor } from "../../models/Descriptor";
import { Plugin } from "../../models/Plugin";
import { Service } from "../../models/Service";
import { RetrievedVim } from "../../models/Vim";

// Snackbar
export const showSnackbar = createAction("Dialogs:Snackbar:show")<string>();
export const resetSnackbar = createAction("Dialogs:Snackbar:reset")();

// Info dialog
export const showInfoDialog = createAction("Dialogs:InfoDialog:show")<{
  title: string;
  message: string;
}>();
export const resetInfoDialog = createAction("Dialogs:InfoDialog:reset")();

// Table dialog
export const resetTableDialog = createAction("Dialogs:TableDialog:reset")();
export const showDescriptorInfoDialog = createAction("Dialogs:TableDialog:showDescriptorInfo")<
  Descriptor
>();
export const showServiceInfoDialog = createAction("Dialogs:TableDialog:showServiceInfo")<Service>();

export const showPluginInfoDialog = createAction("Dialogs:TableDialog:showPluginInfo")<Plugin>();
export const showVimInfoDialog = createAction("Dialogs:TableDialog:showVimInfo")<RetrievedVim>();

// Descriptor editor dialog
export const showDescriptorEditorDialog = createAction("Dialogs:DescriptorEditor:show")<{
  descriptor: Descriptor;
  endpoint: ApiDataEndpoint;
}>();
export const setDescriptorEditorDialogContentString = createAction(
  "Dialogs:DescriptorEditor:setText"
)<string>();
export const resetDescriptorEditorDialog = createAction("Dialogs:DescriptorEditor:reset")();
