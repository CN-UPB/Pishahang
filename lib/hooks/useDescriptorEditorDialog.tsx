import { Button } from "@material-ui/core";
import yaml from "js-yaml";
import dynamic from "next/dynamic";
import * as React from "react";
import { useModal } from "react-modal-hook";
import { boolean } from "yup";

import { updateDescriptor, uploadDescriptor } from "../api/descriptors";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { TextDialog } from "../components/layout/dialogs/TextDialog";
import { Descriptor } from "../models/Descriptor";
import { DescriptorMeta } from "../models/DescriptorMeta";
import { useStateRef } from "./useStateRef";

const DescriptorEditor = dynamic(import("../components/content/DescriptorEditor"), {
  ssr: false,
});

export function useDescriptorEditorDialog(): (string) => void {
  //contains the data of the description form, if any changes were made
  const [formData, setFormData, formDataRef] = useStateRef<string>("");
  const [descriptoMeta, setDescriptorMeta, getDescriptorMeta] = useStateRef<DescriptorMeta>("");
  let hasDataChanged: boolean = false;
  /**
   * Called during any change in the editor
   * @param newValue
   */
  function onChange(newValue) {
    setFormData(newValue);
    hasDataChanged = true;
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
    if (hasDataChanged) {
      //save something only if changes are made
      hideDialog();
      try {
        let convertedDescriptorObject = yaml.safeLoad(formDataRef.current);
        updateDescriptor(convertedDescriptorObject, getDescriptorMeta.current.id);
      } catch (e) {
        console.log("E: " + e);
      }
    } else {
      hideDialog();
    }
  }

  /**
   * Function to
   */
  function confirmClose() {
    if (hasDataChanged) {
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

  return function showDescriptorEditorDialog(descriptorMeta: DescriptorMeta) {
    convertJsonToYML(descriptorMeta);
    setDescriptorMeta(descriptorMeta);
    showDialog();
  };

  /**
   *
   * @param jsonFile Converting json to yaml
   */
  function convertJsonToYML(descriptorMeta: DescriptorMeta) {
    // Get document, or throw exception on error
    try {
      setFormData(yaml.safeDump(descriptorMeta.descriptor));
    } catch (e) {
      console.log("E: " + e);
    }
  }
}
