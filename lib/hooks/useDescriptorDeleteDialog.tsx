import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { TextDialog } from "../components/layout/dialogs/TextDialog";
import { VnfdMeta } from "../models/VnfdMeta";

export function useDescriptorDeleteDialog() {
  let data: VnfdMeta = null;
  /**
   * On Confirmation delete the descriptor and remove it from the Descriptor list
   */
  function deleteDescriptor() {
    //Delete descriptor and update descriptor list
    console.log(data.uuid);
    hideConfirmDialog();
  }

  /**
   * Display a dialog to ask user confirmation...
   */
  const [showConfirmDialog, hideConfirmDialog] = useModal(({ in: open, onExited }) => (
    <TextDialog
      dialogId="ConfirmClose"
      dialogTitle="Delete Descriptor"
      dialogText="Are you sure you want to delete this descriptor?"
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

  return function showDescriptorDeleteDialog(vnfdMeta: VnfdMeta) {
    data = vnfdMeta;
    showConfirmDialog();
  };
}
