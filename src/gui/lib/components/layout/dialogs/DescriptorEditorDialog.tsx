import { Button } from "@material-ui/core";
import dynamic from "next/dynamic";
import * as React from "react";
import { useSelector } from "react-redux";
import { mutate } from "swr";

import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { useThunkDispatch } from "../../../store";
import {
  resetDescriptorEditorDialog,
  setDescriptorEditorDialogContentString,
} from "../../../store/actions/dialogs";
import { selectDescriptorEditorDialog } from "../../../store/selectors/dialogs";
import { updateDescriptor } from "../../../store/thunks/descriptors";
import { GenericDialog } from "./GenericDialog";

const DescriptorEditor = dynamic(import("../../content/DescriptorEditor"), {
  ssr: false,
});

export const DescriptorEditorDialog: React.FunctionComponent = () => {
  const dispatch = useThunkDispatch();
  const { isVisible, descriptor, endpoint, currentContentString } = useSelector(
    selectDescriptorEditorDialog
  );

  const hideDialog = () => dispatch(resetDescriptorEditorDialog());

  const showConfirmationDialog = useGenericConfirmationDialog(
    "Unsaved Changes",
    "Are you sure you want to exit? Your changes will be lost permanently.",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;
      hideDialog();
    },
    "Discard changes"
  );

  const onClose = () => {
    if (currentContentString !== descriptor?.contentString) {
      showConfirmationDialog();
    } else {
      hideDialog();
    }
  };

  const save = async () => {
    if (currentContentString !== descriptor?.contentString) {
      // Update descriptor if changes have been made
      hideDialog();
      await dispatch(
        updateDescriptor(descriptor?.id, currentContentString, {
          successSnackbarMessage: "Descriptor successfully updated",
        })
      );
      mutate(endpoint);
    } else {
      hideDialog();
    }
  };

  return (
    <GenericDialog
      dialogId="descriptor-editor-dialog"
      dialogTitle="Pishahang Descriptor Editor"
      fullWidth
      maxWidth="md"
      open={isVisible}
      onClose={onClose}
      buttons={
        <>
          <Button variant="contained" onClick={save} color="primary" autoFocus>
            Save
          </Button>
          <Button variant="contained" onClick={onClose} color="secondary" autoFocus>
            Cancel
          </Button>
        </>
      }
    >
      <DescriptorEditor
        onChange={(content: string) => dispatch(setDescriptorEditorDialogContentString(content))}
        value={currentContentString}
      />
    </GenericDialog>
  );
};
