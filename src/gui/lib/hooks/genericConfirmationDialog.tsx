import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { TextDialog } from "../components/layout/dialogs/TextDialog";
import { useStateRef } from "./useStateRef";

/**
 * A hook that returns a function (`showDialog`) which shows a customizable confirmation dialog.
 *
 * @param title The title of the dialog
 * @param message The dialog message
 * @param callback A callback function that will be invoked with a boolean stating whether the
 *                 confirm button (`true`) or the cancel button (`false`) was clicked. The other
 *                 parameters are proxied from the invocation of `showDialog`.
 * @param confirmButtonText The caption of the confirmation button
 * @param cancelButtonText The caption of the cancel button
 *
 * @returns A function that will show the dialog. All the parameters will be passed on as additional
 *          parameters to the `callback` function.
 */
export function useGenericConfirmationDialog<P>(
  title: string,
  message: string,
  callback: (confirmed: boolean, ...parameters: P[]) => any,
  confirmButtonText = "Ok",
  cancelButtonText = "Cancel"
) {
  const [parameters, setParameters, parametersRef] = useStateRef<P[]>(null);

  /**
   * Display a dialog to ask user confirmation...
   */
  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => {
    const onButtonClicked = (confirmed: boolean) => {
      callback(confirmed, ...parametersRef.current);
      hideDialog();
    };

    return (
      <TextDialog
        dialogId={"confirm " + title}
        dialogTitle={title}
        dialogText={message}
        open={open}
        onExited={onExited}
        onClose={hideDialog}
        buttons={
          <>
            <Button
              variant="contained"
              onClick={() => onButtonClicked(false)}
              color="secondary"
              autoFocus
            >
              {cancelButtonText}
            </Button>
            <Button
              variant="contained"
              onClick={() => onButtonClicked(true)}
              color="primary"
              autoFocus
            >
              {confirmButtonText}
            </Button>
          </>
        }
      ></TextDialog>
    );
  });

  return (...parameters: P[]) => {
    setParameters(parameters);
    showDialog();
  };
}
