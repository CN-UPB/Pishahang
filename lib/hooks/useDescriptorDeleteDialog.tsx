import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { deleteDescriptor } from "../api/descriptors";
import { TextDialog } from "../components/layout/dialogs/TextDialog";
import { useStateRef } from "./useStateRef";

export function useDescriptorDeleteDialog() {
  let descriptorUUID: string;
  const [formData, setFormData, formDataRef] = useStateRef<string>("");
  /**
   * On Confirmation delete the descriptor and remove it from the Descriptor list
   */
  function sendDeleteDescriptorRequest() {
    //Delete descriptor and update descriptor list
    hideConfirmDialog();
    deleteDescriptor(formDataRef.current);
  }

  /**
   * Display a dialog to ask user confirmation...
   */
  const [showConfirmDialog, hideConfirmDialog] = useModal(({ in: open, onExited }) => (
    <TextDialog
      dialogId="ConfirmClose"
      dialogTitle="Delete Descriptor"
      dialogText={"Are you sure, you want to delete this descriptor?"}
      open={open}
      onExited={onExited}
      onClose={hideConfirmDialog}
      buttons={
        <>
          <Button variant="contained" onClick={hideConfirmDialog} color="secondary" autoFocus>
            no
          </Button>
          <Button
            variant="contained"
            onClick={sendDeleteDescriptorRequest}
            color="primary"
            autoFocus
          >
            yes
          </Button>
        </>
      }
    ></TextDialog>
  ));

  return function showDescriptorDeleteDialog(uuid: string) {
    setFormData(uuid);
    showConfirmDialog();
  };
}
