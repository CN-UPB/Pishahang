import { Dialog, DialogActions, DialogContent, DialogTitle } from "@material-ui/core";
import { DialogProps } from "@material-ui/core/Dialog";
import * as React from "react";

export type GenericDialogProps = DialogProps & {
  /**
   * A unique id prefix to be used internally for `aria` properties.
   */
  dialogId: string;
  /**
   * The dialog's title.
   */
  dialogTitle: string;
  buttons: React.ReactFragment;
};

export const GenericDialog: React.FunctionComponent<GenericDialogProps> = ({
  dialogId,
  dialogTitle,
  buttons,
  children,
  ...dialogProps
}) => (
  <Dialog aria-labelledby={dialogId + "-dialog-title"} {...dialogProps}>
    <DialogTitle id={dialogId + "-dialog-title"}>{dialogTitle}</DialogTitle>
    <DialogContent>{children}</DialogContent>
    <DialogActions>{buttons}</DialogActions>
  </Dialog>
);
