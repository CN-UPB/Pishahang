import { DialogProps } from "@material-ui/core/Dialog";
import * as React from "react";
import {
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Dialog,
} from "@material-ui/core";

export type TextDialogProps = DialogProps & {
  /**
   * A unique id prefix to be used internally for `aria` properties.
   */
  dialogId: string;
  /**
   * The dialog's title.
   */
  dialogTitle: string;
  /**
   * The dialog's text content.
   */
  dialogText: string;
  buttons: React.ReactFragment;
};

export const TextDialog: React.FunctionComponent<TextDialogProps> = ({
  dialogId,
  dialogTitle,
  dialogText,
  buttons,
  ...dialogProps
}) => (
  <Dialog
    {...dialogProps}
    aria-labelledby={dialogId + "-dialog-title"}
    aria-describedby={dialogId + "-dialog-description"}
  >
    <DialogTitle id={dialogId + "-dialog-title"}>{dialogTitle}</DialogTitle>
    <DialogContent>
      <DialogContentText id={dialogId + "-dialog-description"}>{dialogText}</DialogContentText>
    </DialogContent>
    <DialogActions>{buttons}</DialogActions>
  </Dialog>
);
