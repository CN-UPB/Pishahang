import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";
import { useDispatch } from "react-redux";

import { uploadDescriptor } from "../api/descriptors";
import { FileSelector } from "../components/content/FileSelector";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { DescriptorType } from "../models/Descriptor";
import { showSnackbar } from "../store/actions/global";

export function useDescriptorUploadDialog(descriptorType: DescriptorType) {
  const dispatch = useDispatch();

  const acceptedFiles = []; //Cannot get this to only allow for .yaml files upload
  /**
   * Display a dialog for uploading Descriptors...
   */
  let readFile;
  let type = descriptorType;
  function onDrop(files) {
    const blb = new Blob([files], { type: "text/json" });
    var file = new File([blb], "descriptor", { type: "text/json;charset=utf-8" });
    const reader = new FileReader();

    reader.onload = e => {
      var text = reader.result.toString();
      readFile = JSON.parse(text);
    };

    // Start reading the blob as text.
    reader.readAsText(file);
  }

  function upload() {
    hideFileSelector();
    uploadDescriptor(type, readFile);
    dispatch(showSnackbar("Uploaded"));
  }

  const [showFileSelector, hideFileSelector] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="uploader"
      dialogTitle="Pishahang Descriptor Uploader"
      open={open}
      onExited={onExited}
      onClose={hideFileSelector}
      buttons={
        <>
          <Button variant="contained" onClick={upload} color="primary" autoFocus>
            Upload
          </Button>
        </>
      }
    >
      <FileSelector
        acceptedFiles={acceptedFiles}
        maxFileSize={10}
        showPreviews={false}
        showAlerts={true}
        filesLimit={1}
        dropzoneText={"Drag or Click"}
        onDrop={onDrop}
        showFileNames={true}
      ></FileSelector>
    </GenericDialog>
  ));

  return function showDescriptorUploadDialog() {
    showFileSelector();
  };
}
