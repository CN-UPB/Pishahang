import { useDispatch } from "react-redux";

import { deleteDescriptor } from "../api/descriptors";
import { showInfoDialog, showSnackbar } from "../store/actions/dialogs";
import { useGenericConfirmationDialog } from "./genericConfirmationDialog";

/**
 * Returns a function `showDescriptorDeleteDialog` that can be called with a descriptor
 * id to show a confirmation dialog. If the user confirms the deletion, the given
 * descriptor will be deleted and the provided `onDeleted` function will be called.
 */
export function useDescriptorDeleteDialog(onDeleted: () => Promise<any>) {
  const dispatch = useDispatch();

  return useGenericConfirmationDialog(
    "Delete Descriptor?",
    "Are you sure you want to delete this descriptor? This cannot be undone.",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;

      const reply = await deleteDescriptor(id);
      if (reply.success) {
        dispatch(showSnackbar("Descriptor successfully deleted"));
        await onDeleted();
      } else {
        dispatch(showInfoDialog({ title: "Error", message: reply.message }));
      }
    },
    "Delete Descriptor"
  );
}
