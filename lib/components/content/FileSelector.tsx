import { DropzoneArea } from "material-ui-dropzone";
import * as React from "react";

type Props = {
  /** Maximum number of files that can be loaded into the dropzone*/
  filesLimit: number;
  /** Shows previews BELOW the Dropzone*/
  showPreviews: boolean;
  /** Text in dropzone*/
  dropzoneText: string;
  /** Maximum file size (in MB) that the dropzone will accept*/
  maxFileSize: number;
  /** Shows styled snackbar alerts when files are dropped, deleted or rejected.*/
  showAlerts: boolean;
  /** A list of file mime types to accept. Does support wildcards. e.g. 'image/*', 'video/*', 'application/*'*/
  acceptedFiles: string[];
};

export const FileSelector: React.FunctionComponent<Props> = props => {
  let fileSizeInBytes = props.maxFileSize * 1048576;
  function handleChange(files) {
    let data = files;
    console.log(data);
  }

  return (
    <DropzoneArea
      dropzoneText={props.dropzoneText}
      acceptedFiles={props.acceptedFiles}
      filesLimit={props.filesLimit}
      maxFileSize={fileSizeInBytes}
      showPreviewsInDropzone={true}
      showFileNamesInPreview={true}
      showPreviews={props.showPreviews}
      onChange={handleChange}
    />
  );
};
