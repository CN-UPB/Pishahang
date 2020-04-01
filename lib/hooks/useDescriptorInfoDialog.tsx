import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { InfoDialogTable } from "../components/layout/tables/InfoDialogTable";
import { Descriptor } from "../models/Descriptor";
import { useStateRef } from "./useStateRef";

export function useDescriptorInfoDialog() {
  const [descriptor, setDescriptor, descriptorRef] = useStateRef<Descriptor>(null);
  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => {
    const currentDescriptor = descriptorRef.current;
    return (
      <GenericDialog
        dialogId="descriptorInfo"
        dialogTitle={descriptorRef.current.content.name}
        open={open}
        onExited={onExited}
        onClose={hideDialog}
        buttons={
          <>
            <Button variant="contained" onClick={hideDialog} color="secondary" autoFocus>
              Close
            </Button>
          </>
        }
      >
        <InfoDialogTable
          content={[
            ["Description", ""],
            ["Vendor", currentDescriptor.content.vendor],
            ["Name", currentDescriptor.content.name],
            ["Version", currentDescriptor.content.version],
            ["Created at", currentDescriptor.createdAt],
            ["Updated at", currentDescriptor.updatedAt],
            ["ID", currentDescriptor.id],
          ]}
        />
      </GenericDialog>
    );
  });

  return function showVnfdInfoDialog(descriptorMeta: Descriptor) {
    setDescriptor(descriptorMeta);
    showDialog();
  };
}
