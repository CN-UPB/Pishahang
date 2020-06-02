import * as React from "react";
import { useModal } from "react-modal-hook";

import { UserProfile } from "../components/forms/userprofile";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";

export function useAddUserDialog() {
  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="User"
      dialogTitle={"Add User"}
      open={open}
      onExited={onExited}
      onClose={hideDialog}
      buttons={<></>}
    >
      <UserProfile></UserProfile>
    </GenericDialog>
  ));

  return function showAddUserDialog() {
    showDialog();
  };
}
