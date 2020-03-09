import { Button } from "@material-ui/core";
import dynamic from "next/dynamic";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { TextDialog } from "../components/layout/dialogs/TextDialog";
import { useStateRef } from "./useStateRef";

const DescriptorEditor = dynamic(import("../components/content/DescriptorEditor"), {
  ssr: false,
});

export function useDescriptorEditorDialog(): () => void {
  //contains the data of the description form, if any changes were made
  const [formData, setFormData, formDataRef] = useStateRef<string>("");
  /**
   * Called during any change in the editor
   * @param newValue
   */
  function onChange(newValue) {
    setFormData(newValue);
  }

  /**
   * Sets changes on load of the editor
   * @param newValue
   */
  function onLoad(newValue) {}

  /**
   * Function for saving modified file
   */
  function onSave() {
    if (formDataRef.current !== "") {
      //save something only if changes are made
      hideDialog();
      setFormData("");
    } else {
      hideDialog();
      setFormData("");
    }
  }

  /**
   * Function to
   */
  function confirmClose() {
    if (formDataRef.current !== "") {
      //confirm close
      showConfirmDialog();
    } else {
      hideDialog();
    }
  }

  /**
   * Function to close confirmation dialog and set value of formData to null
   */
  function closeConfirmationDialog() {
    hideConfirmDialog();
    hideDialog();
    setFormData("");
  }

  /**
   * Display a dialog to ask user confirmation...
   */
  const [showConfirmDialog, hideConfirmDialog] = useModal(({ in: open, onExited }) => (
    <TextDialog
      dialogId="ConfirmClose"
      dialogTitle="Un-Saved Changes!"
      dialogText="Are you sure you want to exit?"
      open={open}
      onExited={onExited}
      onClose={hideConfirmDialog}
      buttons={
        <>
          <Button variant="contained" onClick={hideConfirmDialog} color="secondary" autoFocus>
            no
          </Button>
          <Button variant="contained" onClick={closeConfirmationDialog} color="primary" autoFocus>
            yes
          </Button>
        </>
      }
    ></TextDialog>
  ));

  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="vnfdInfo"
      dialogTitle="Pishahang Descriptor Editor"
      open={open}
      onExited={onExited}
      onClose={hideDialog}
      buttons={
        <>
          <Button variant="contained" onClick={onSave} color="primary" autoFocus>
            Save
          </Button>
          <Button variant="contained" onClick={confirmClose} color="secondary" autoFocus>
            Close
          </Button>
        </>
      }
    >
      <DescriptorEditor
        onChange={onChange}
        onLoad={onLoad}
        value={formDataRef.current}
        lan="javascript"
        theme="twilight"
      ></DescriptorEditor>
    </GenericDialog>
  ));

  return function showDescriptorEditorDialog() {
    showDialog();
  };
}
