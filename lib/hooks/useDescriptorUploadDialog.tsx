import { Button } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { FileSelector } from "../components/content/FileSelector";
import { GenericDialog } from "../components/layout/dialogs/GenericDialog";

export function useDescriptorUploadDialog() {
  const acceptedFiles = []; //Cannot get this to only allow for .yaml files upload
  /**
   * Display a dialog for uploading Descriptors...
   */
  const [showFileSelector, hideFileSelector] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="uploader"
      dialogTitle="Pishahang Descriptor Uploader"
      open={open}
      onExited={onExited}
      onClose={hideFileSelector}
      buttons={
        <>
          <Button variant="contained" onClick={hideFileSelector} color="primary" autoFocus>
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
      ></FileSelector>
    </GenericDialog>
  ));

  return function showDescriptorUploadDialog() {
    showFileSelector();
  };
}
