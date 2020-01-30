import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { VnfdMeta } from "../models/VnfdMeta";

export function useVnfdInfoDialog(): (vnfdMeta: VnfdMeta) => void {
  let data: VnfdMeta = null;
  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="vnfdInfo"
      dialogTitle={data.descriptor.name}
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
      {data.descriptor.description}
    </GenericDialog>
  ));

  return function showVnfdInfoDialog(vnfdMeta: VnfdMeta) {
    data = vnfdMeta;

    showDialog();
  };
}
