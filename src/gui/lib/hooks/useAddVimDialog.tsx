import { Box, Button } from "@material-ui/core";
import { FormikValues } from "formik";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { VimForm, VimFormValues } from "../components/forms/VimForm";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { NewVim, VimType } from "../models/Vim";
import { useThunkDispatch } from "../store";
import { addVim } from "../store/thunks/vims";

export function useAddVimDialog(onVimAdded: () => Promise<any>) {
  const formikRef = React.useRef<FormikValues>();
  const dispatch = useThunkDispatch();

  const submit = () => {
    formikRef.current.handleSubmit();
  };

  const onSubmit = async (values: VimFormValues) => {
    const { openstack, aws, kubernetes, ...common } = values as Omit<VimFormValues, "type"> & {
      type: VimType;
    }; // Yup has already made sure that VimType is not an empty string

    let vim: NewVim;
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
    const reply = await dispatch(addVim(vim, { successSnackbarMessage: "VIM successfully added" }));
    if (reply.success) {
      hideDialog();
      await onVimAdded();
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
          <Button variant="contained" onClick={hideDialog} color="secondary">
            Cancel
          </Button>
          <Button variant="contained" onClick={submit} color="primary">
            Add
          </Button>
        </>
      }
    >
      <Box marginBottom={2}>
        <VimForm formikRef={formikRef} onSubmit={onSubmit}></VimForm>
      </Box>
    </GenericDialog>
  ));

  return showDialog;
}
