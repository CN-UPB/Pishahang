import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@material-ui/core";
import { DialogProps } from "@material-ui/core/Dialog";
import * as React from "react";

/**
 * Generic Dialogue
 */
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

/**
 * Generic Dialog for cutomizability
 */
export const GenericDialog: React.FunctionComponent<GenericDialogProps> = ({
  dialogId,
  dialogTitle,
  buttons,
  children,
  ...dialogProps
}) => (
  <Dialog
    {...dialogProps}
    aria-labelledby={dialogId + "-dialog-title"}
    aria-describedby={dialogId + "-dialog-description"}
  >
    <DialogTitle id={dialogId + "-dialog-title"}>{dialogTitle}</DialogTitle>
    <DialogContent>{children}</DialogContent>
    <DialogActions>{buttons}</DialogActions>
  </Dialog>
);
