import { Button } from "@material-ui/core";
import yaml from "js-yaml";
import dynamic from "next/dynamic";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { TextDialog } from "../components/layout/dialogs/TextDialog";
import { Descriptor, DescriptorContent } from "../models/Descriptor";
import { useThunkDispatch } from "../store";
import { updateDescriptor } from "../store/thunks/descriptors";
import { convertJsonToYaml } from "../util/yaml";
import { useStateRef } from "./useStateRef";

const DescriptorEditor = dynamic(import("../components/content/DescriptorEditor"), {
  ssr: false,
});

export function useDescriptorEditorDialog(): (string) => void {
  //contains the data of the description form, if any changes were made
  const [formData, setFormData, formDataRef] = useStateRef<string>("");
  const [descriptor, setDescriptor, descriptorRef] = useStateRef<Descriptor>();
  const dispatch = useThunkDispatch();
  let hasDataChanged: boolean = false;

  /**
   * Called during any change in the editor
   * @param newValue
   */
  function onChange(newValue: string) {
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
  const onSave = async () => {
    if (hasDataChanged) {
      //save something only if changes are made
      hideDialog();
      let descriptorContent = yaml.safeLoad(formDataRef.current) as DescriptorContent;
      await dispatch(
        updateDescriptor(descriptorContent, descriptorRef.current.id, {
          showErrorInfoDialog: true,
          successSnackbarMessage: "Descriptor successfully updated",
        })
      );
    } else {
      hideDialog();
    }
  };

  /**
   * Function to ask closing confirmation
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
      dialogId="confirm-close"
      dialogTitle="Unsaved Changes!"
      dialogText="Are you sure you want to exit? Your changes will be lost permanently."
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

  return function showDescriptorEditorDialog(descriptor: Descriptor) {
    const yamlString = convertJsonToYaml(descriptor.content);
    setFormData(yamlString);
    setDescriptor(descriptor);
    showDialog();
  };
}
