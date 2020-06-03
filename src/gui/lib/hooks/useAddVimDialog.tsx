import { Box, Button, Container } from "@material-ui/core";
import { FormikValues } from "formik";
import * as React from "react";
import { useModal } from "react-modal-hook";
import { useDispatch } from "react-redux";

import { addVim } from "../api/vims";
import { VimForm, VimFormValues } from "../components/forms/VimForm";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { VimType } from "../models/Vims";
import { showInfoDialog, showSnackbar } from "../store/actions/dialogs";

export function useAddVimDialog(onVimAdded: () => Promise<any>) {
  const formikRef = React.useRef<FormikValues>();
  const dispatch = useDispatch();

  const submit = () => {
    formikRef.current.handleSubmit();
  };

  const onSubmit = async (values: VimFormValues) => {
    const { openstack, aws, kubernetes, ...common } = values;

    let vim: any;
    switch (values.type) {
      case VimType.OpenStack:
        vim = { ...openstack, ...common };
        break;

      case VimType.Kubernetes:
        vim = { ...kubernetes, ...common };
        break;

      case VimType.Aws:
        vim = { ...aws, ...common };
        break;
    }
    const reply = await addVim(vim);
    if (reply.success) {
      hideDialog();
      dispatch(showSnackbar("VIM successfully added"));
      await onVimAdded();
    } else {
      dispatch(showInfoDialog({ title: "Error", message: reply.message }));
    }
  };

  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="add-vim-dialog"
      dialogTitle={"Add a VIM"}
      open={open}
      onExited={onExited}
      onClose={hideDialog}
      disableBackdropClick
      buttons={
        <>
          <Button variant="contained" onClick={submit} color="primary">
            Add
          </Button>
          <Button variant="contained" onClick={hideDialog} color="secondary">
            Cancel
          </Button>
        </>
      }
    >
      <Container maxWidth="md">
        <Box marginBottom={2}>
          <VimForm formikRef={formikRef} onSubmit={onSubmit}></VimForm>
        </Box>
      </Container>
    </GenericDialog>
  ));

  return showDialog;
}
