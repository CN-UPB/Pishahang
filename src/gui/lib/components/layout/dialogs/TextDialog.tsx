import { DialogContentText } from "@material-ui/core";
import * as React from "react";

import { GenericDialog, GenericDialogProps } from "./GenericDialog";

export type TextDialogProps = GenericDialogProps & {
  /**
   * The dialog's text content.
   */
  dialogText: string;
};

export const TextDialog: React.FunctionComponent<TextDialogProps> = ({
  dialogText,
  ...dialogProps
}) => (
  <GenericDialog {...dialogProps} aria-describedby={dialogProps.dialogId + "-dialog-description"}>
    <DialogContentText id={dialogProps.dialogId + "-dialog-description"}>
      {dialogText}
    </DialogContentText>
  </GenericDialog>
);
