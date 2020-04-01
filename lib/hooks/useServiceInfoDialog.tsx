import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { InfoDialogTable } from "../components/layout/tables/InfoDialogTable";
import { Service } from "../models/Service";
import { useStateRef } from "./useStateRef";

export function useServiceInfoDialog() {
  const [service, setService, serviceRef] = useStateRef<Service>(null);
  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => {
    const currentService = serviceRef.current;
    return (
      <GenericDialog
        dialogId="serviceInfo"
        dialogTitle={serviceRef.current.name}
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
            ["Vendor", currentService.vendor],
            ["Name", currentService.name],
            ["Description", ""],
            ["Version", currentService.version],
            ["Created at", currentService.createdAt],
            ["Version", currentService.version],
            ["Service Id", currentService.id],
          ]}
        />
      </GenericDialog>
    );
  });

  return function showServiceInfoDialog(service: Service) {
    setService(service);
    showDialog();
  };
}
