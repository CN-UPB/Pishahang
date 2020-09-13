/** @jsx jsx */
import { jsx } from "@emotion/core";
import { useTheme } from "@material-ui/core";
import { CloudUpload } from "@material-ui/icons";
import * as React from "react";
import FileReaderInput from "react-file-reader-input";

import { DescriptorType } from "../../models/Descriptor";
import { useThunkDispatch } from "../../store";
import { showInfoDialog } from "../../store/actions/dialogs";
import { uploadDescriptor } from "../../store/thunks/descriptors";

type Props = {
  descriptorType: DescriptorType;
  onUploaded: () => Promise<any>;
};

export const DescriptorUploadButton: React.FunctionComponent<Props> = ({
  descriptorType,
  onUploaded,
}) => {
  const dispatch = useThunkDispatch();
  const theme = useTheme();

  const upload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    [[progressEvent, file]]: FileReaderInput.Result[]
  ) => {
    const contentString = await file.text();
    try {
      const reply = await dispatch(
        uploadDescriptor(descriptorType, contentString, {
          successSnackbarMessage: "Descriptor successfully uploaded",
        })
      );
      if (reply.success) {
        await onUploaded();
      }
    } catch {
      dispatch(
        showInfoDialog({
          title: "Error",
          message:
            "An error ocurred while parsing the selected descriptor file. " +
            "Please make sure the file you upload is a valid YAML file.",
        })
      );
      return;
    }
  };

  return (
    <FileReaderInput
      as="text"
      accept=".yml,.yaml"
      onChange={upload}
      css={{ display: "none" }} // Hide <input> element
      style={{ display: "inline-flex" }}
    >
      <CloudUpload htmlColor={theme.palette.primary.main} />
    </FileReaderInput>
  );
};
