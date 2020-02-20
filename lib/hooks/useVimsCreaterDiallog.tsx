import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { VimForm } from "../components/forms/vims/VimForm";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";

export function useVimsCreaterDialog() {
  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="Vims"
      dialogTitle={""}
      open={open}
      onExited={onExited}
      onClose={hideDialog}
      buttons={
        <>
          <Button variant="contained" onClick={hideDialog} color="secondary" autoFocus>
            close
          </Button>
        </>
      }
    >
      <VimForm />
    </GenericDialog>
  ));

  return function showVimsCreaterDialog() {
    showDialog();
  };
}
