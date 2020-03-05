import { DropzoneArea, DropzoneAreaProps } from "material-ui-dropzone";
import * as React from "react";

type Props = {
  /** Maximum file size (in MB) that the dropzone will accept*/
  maxFileSize: number;
} & Omit<DropzoneAreaProps, "maxFileSize">;

export const FileSelector: React.FunctionComponent<Props> = ({ maxFileSize, ...props }) => {
  let fileSizeInBytes = maxFileSize * 1048576;

  return (
    <DropzoneArea
      maxFileSize={fileSizeInBytes}
      showPreviewsInDropzone={true}
      showFileNamesInPreview={true}
      {...props}
    />
  );
};
