import { Box, Button } from "@material-ui/core";
import { FormikValues } from "formik";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { InstantiationForm, InstantiationFormValues } from "../components/forms/InstantiationForm";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { Service } from "../models/Service";
import { useThunkDispatch } from "../store";
import { instantiateService } from "../store/thunks/services";
import { useStateRef } from "./useStateRef";

export function useInstantiationDialog(onRequestSucceeded: (service: Service) => Promise<any>) {
  const formikRef = React.useRef<FormikValues>();
  const dispatch = useThunkDispatch();
  const [, setService, serviceRef] = useStateRef<Service>();

  const submit = () => {
    formikRef.current.handleSubmit();
  };

  const onSubmit = async (values: InstantiationFormValues) => {
    const reply = await dispatch(
      instantiateService(
        serviceRef.current.id,
        values.ingresses.split(","),
        values.egresses.split(",")
      )
    );
    if (reply.success) {
      hideDialog();
      await onRequestSucceeded(serviceRef.current);
    }
  };

  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="instantiate-service-dialog"
      dialogTitle={`Instantiate ${serviceRef.current.name}`}
      open={open}
      onExited={onExited}
      onClose={hideDialog}
      disableBackdropClick
      buttons={
        <>
          <Button variant="contained" onClick={hideDialog} color="secondary">
            Cancel
          </Button>
          <Button variant="contained" onClick={submit} color="primary">
            Instantiate
          </Button>
        </>
      }
    >
      <Box marginBottom={2}>
        <InstantiationForm formikRef={formikRef} onSubmit={onSubmit}></InstantiationForm>
      </Box>
    </GenericDialog>
  ));

  return (service: Service) => {
    setService(service);
    showDialog();
  };
}
