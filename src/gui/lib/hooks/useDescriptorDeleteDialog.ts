import { useThunkDispatch } from "./../store/index";
import { deleteDescriptor } from "../store/thunks/descriptors";
import { useGenericConfirmationDialog } from "./genericConfirmationDialog";

/**
 * Returns a function `showDescriptorDeleteDialog` that can be called with a descriptor
 * id to show a confirmation dialog. If the user confirms the deletion, the given
 * descriptor will be deleted and the provided `onDeleted` function will be called.
 */
export function useDescriptorDeleteDialog(onDeleted: () => Promise<any>) {
  const dispatch = useThunkDispatch();

  return useGenericConfirmationDialog(
    "Delete Descriptor?",
    "Are you sure you want to delete this descriptor? This cannot be undone.",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;
      const reply = await dispatch(
        deleteDescriptor(id, {
          showErrorInfoDialog: true,
          successSnackbarMessage: "Descriptor successfully deleted",
        })
      );
      if (reply.success) {
        await onDeleted();
      }
    },
    "Delete Descriptor"
  );
}
