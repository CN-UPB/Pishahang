import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { TextDialog } from "../components/layout/dialogs/TextDialog";

export function useDescriptorDeleteDialog() {
  let descriptorUUID,
    descriptorName: string = "";
  let dialogText =
    "Are you sure you want to delete descriptor\nName: " +
    { descriptorName } +
    "\nUUID: " +
    { descriptorUUID };

  console.log(
    "Are you sure you want to delete descriptor\nName: " +
      descriptorName +
      "\nUUID: " +
      descriptorUUID
  );

  /**
   * On Confirmation delete the descriptor and remove it from the Descriptor list
   */
  function deleteDescriptor() {
    //Delete descriptor and update descriptor list
    console.log(descriptorUUID);
    hideConfirmDialog();
  }

  /**
   * Display a dialog to ask user confirmation...
   */
  const [showConfirmDialog, hideConfirmDialog] = useModal(({ in: open, onExited }) => (
    <TextDialog
      dialogId="ConfirmClose"
      dialogTitle="Delete Descriptor"
      dialogText={dialogText}
      open={open}
      onExited={onExited}
      onClose={hideConfirmDialog}
      buttons={
        <>
          <Button variant="contained" onClick={hideConfirmDialog} color="secondary" autoFocus>
            no
          </Button>
          <Button variant="contained" onClick={deleteDescriptor} color="primary" autoFocus>
            yes
          </Button>
        </>
      }
    ></TextDialog>
  ));

  return function showDescriptorDeleteDialog(uuid: string, name: string) {
    descriptorUUID = uuid;
    descriptorName = name;

    console.log(
      "Are you sure you want to delete descriptor\nName: " +
        descriptorName +
        "\nUUID: " +
        descriptorUUID
    );
    showConfirmDialog();
  };
}
