import { Tooltip } from "@material-ui/core";
import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";

import { useDescriptorUploadDialog } from "../../hooks/useDescriptorUploadDialog";
import { DescriptorType } from "../../models/Descriptor";
import {
  AwsFunctionDescriptorTable,
  KubernetesFunctionDescriptorTable,
  OpenStackFunctionDescriptorTable,
} from "../layout/tables/FunctionDescriptorTable";
import { ServiceDescriptorTable } from "../layout/tables/ServiceDescriptorTable";

type Props = {
  type: DescriptorType;
};

export const DescriptorPageContent: React.FunctionComponent<Props> = ({ type }) => {
  const showDescriptorUploadDialog = useDescriptorUploadDialog(type);

  return (
    <>
      <Tooltip title="Upload" arrow>
        <Fab
          color="primary"
          size="small"
          style={{ float: "right" }}
          aria-label="Upload"
          onClick={showDescriptorUploadDialog}
        >
          <CloudUpload />
        </Fab>
      </Tooltip>
      {type == DescriptorType.Service && <ServiceDescriptorTable></ServiceDescriptorTable>}
      {type == DescriptorType.OPENSTACK && (
        <OpenStackFunctionDescriptorTable></OpenStackFunctionDescriptorTable>
      )}
      {type == DescriptorType.KUBERNETES && (
        <KubernetesFunctionDescriptorTable></KubernetesFunctionDescriptorTable>
      )}
      {type == DescriptorType.AWS && <AwsFunctionDescriptorTable></AwsFunctionDescriptorTable>}
    </>
  );
};
