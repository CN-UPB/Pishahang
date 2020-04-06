import { createAction } from "typesafe-actions";

import { Descriptor } from "../../models/Descriptor";
import { Service } from "../../models/Service";

export const showSnackbar = createAction("Dialogs:Snackbar:show")<string>();
export const resetSnackbar = createAction("Dialogs:Snackbar:reset")();

export const showInfoDialog = createAction("Dialogs:InfoDialog:show")<{
  title: string;
  message: string;
}>();
export const resetInfoDialog = createAction("Dialogs:InfoDialog:reset")();

export const resetTableDialog = createAction("Dialogs:TableDialog:reset")();
export const showDescriptorInfoDialog = createAction("Dialogs:TableDialog:showDescriptorInfo")<
  Descriptor
>();
export const showServiceInfoDialog = createAction("Dialogs:TableDialog:showServiceInfo")<Service>();
