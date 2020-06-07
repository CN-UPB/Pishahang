import { Fab, Tooltip } from "@material-ui/core";
import { CloudUpload } from "@material-ui/icons";
import yaml from "js-yaml";
import * as React from "react";
import FileReaderInput from "react-file-reader-input";

import { DescriptorContent, DescriptorType } from "../../models/Descriptor";
import { useThunkDispatch } from "../../store";
import { showInfoDialog } from "../../store/actions/dialogs";
import { uploadDescriptor } from "../../store/thunks/descriptors";

type Props = {
  descriptorType: DescriptorType;
  onUploaded: () => Promise<any>;
};

export const DescriptorUploadButton: React.FunctionComponent<Props> = (
  { descriptorType, onUploaded },
  ref
) => {
  const dispatch = useThunkDispatch();

  const upload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    [[progressEvent, file]]: FileReaderInput.Result[]
  ) => {
    const contentString = await file.text();
    let content: DescriptorContent;
    try {
      content = yaml.safeLoad(contentString);
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

    const reply = await dispatch(
      uploadDescriptor(descriptorType, content, contentString, {
        successSnackbarMessage: "Descriptor successfully uploaded",
      })
    );
    if (reply.success) {
      await onUploaded();
    }
  };

  return (
    // @ts-ignore https://github.com/DefinitelyTyped/DefinitelyTyped/pull/45268
    <FileReaderInput as="text" accept=".yml,.yaml" onChange={upload}>
      <Tooltip
        title={`Upload a ${
          descriptorType == DescriptorType.Service ? "service" : "function"
        } descriptor`}
        arrow
      >
        <Fab
          color="primary"
          size="small"
          style={{ float: "right", marginBottom: "0px" }}
          aria-label="Upload"
          component="label"
        >
          <CloudUpload />
        </Fab>
      </Tooltip>
    </FileReaderInput>
  );
};
