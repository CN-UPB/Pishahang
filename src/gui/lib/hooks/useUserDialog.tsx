import { Box, Button } from "@material-ui/core";
import { FormikValues } from "formik";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { UserForm, UserFormProps } from "../components/forms/UserForm";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { LocalUser, User } from "../models/User";
import { useStateRef } from "./useStateRef";

/**
 * A generic user data form dialog that can be used to add or edit users.
 *
 * @param onSubmit Async function that is invoked when the submit button is clicked. The dialog will
 * be closed afterwards if it returns true, and will remain open otherwise.
 *
 */
export function useUserDialog(
  buttonText: string,
  onSubmit: (values: LocalUser) => Promise<boolean>,
  hideIsAdminSwitch: boolean = false
) {
  const formikRef = React.useRef<FormikValues>();
  const [initialValues, setInitialValues, initialValuesRef] = useStateRef<User>();

  const submit = () => {
    formikRef.current.handleSubmit();
  };

  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="user-dialog"
      dialogTitle={buttonText + " user "}
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
            {buttonText}
          </Button>
        </>
      }
    >
      <Box marginBottom={2}>
        <UserForm
          formikRef={formikRef}
          onSubmit={async (values) => {
            if (await onSubmit(values)) {
              hideDialog();
            }
          }}
          initialValues={initialValuesRef.current}
          hideIsAdminSwitch={hideIsAdminSwitch}
        />
      </Box>
    </GenericDialog>
  ));

  // return showDialog;
  return function showUserEditorDialog(initialValues?: User) {
    setInitialValues(initialValues);
    showDialog();
  };
}
