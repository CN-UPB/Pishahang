import { Box, Button } from "@material-ui/core";
import { FormikValues } from "formik";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { UserForm, UserFormProps } from "../components/forms/UserForm";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";

/**
 * A generic user data form dialog that can be used to add or edit users.
 *
 * @param userFormProps The props for the underlying `UserForm` component
 */
export function useUserDialog(userFormProps: Omit<UserFormProps, "formikRef">) {
  const formikRef = React.useRef<FormikValues>();

  const submit = () => {
    formikRef.current.handleSubmit();
  };

  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="add-user-dialog"
      dialogTitle={"Add a user"}
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
        <UserForm formikRef={formikRef} {...userFormProps}></UserForm>
      </Box>
    </GenericDialog>
  ));

  return showDialog;
}
