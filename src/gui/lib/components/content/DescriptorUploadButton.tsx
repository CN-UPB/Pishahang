import { Fab } from "@material-ui/core";
import { CloudUpload } from "@material-ui/icons";
import yaml from "js-yaml";
import * as React from "react";
import FileReaderInput from "react-file-reader-input";
import { useDispatch } from "react-redux";

import { uploadDescriptor } from "../../api/descriptors";
import { DescriptorType } from "../../models/Descriptor";
import { showInfoDialog, showSnackbar } from "../../store/actions/dialogs";

type Props = {
  descriptorType: DescriptorType;
  onUploaded: () => Promise<any>;
};

export const DescriptorUploadButton: React.FunctionComponent<Props> = ({
  descriptorType,
  onUploaded,
}) => {
  const dispatch = useDispatch();

  const upload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    [[progressEvent, file]]: FileReaderInput.Result[]
  ) => {
    const contentString = await file.text();
    const content = yaml.safeLoad(contentString);

    const reply = await uploadDescriptor(descriptorType, content, contentString);
    if (reply.success) {
      dispatch(showSnackbar("Descriptor successfully uploaded"));
      await onUploaded();
    } else {
      dispatch(showInfoDialog({ title: "Error", message: reply.message }));
    }
  };

  return (
    //@ts-ignore https://github.com/DefinitelyTyped/DefinitelyTyped/pull/45268
    <FileReaderInput as="text" accept=".yml,.yaml" onChange={upload}>
      <Fab
        color="primary"
        size="small"
        style={{ float: "right" }}
        aria-label="Upload"
        component="label"
      >
        <CloudUpload />
      </Fab>
    </FileReaderInput>
  );
};
