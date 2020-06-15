import { useTheme } from "@material-ui/core/styles";
import { DeleteForeverRounded, Edit, Info } from "@material-ui/icons";
import * as React from "react";
import { useDispatch } from "react-redux";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useDescriptorEditorDialog } from "../../../hooks/useDescriptorEditorDialog";
import { Descriptor, DescriptorType } from "../../../models/Descriptor";
import { showDescriptorInfoDialog } from "../../../store/actions/dialogs";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";
import { DescriptorUploadButton } from "../DescriptorUploadButton";

type Props = { descriptorType: DescriptorType };

export const FunctionDescriptorTable: React.FunctionComponent<Props> = ({ descriptorType }) => {
  let endpoint: ApiDataEndpoint;
  let uploadTooltip: string;
  switch (descriptorType) {
    case DescriptorType.OPENSTACK:
      endpoint = ApiDataEndpoint.OpenStackFunctionDescriptors;
      uploadTooltip = "Upload an OpenStack descriptor";
      break;

    case DescriptorType.KUBERNETES:
      endpoint = ApiDataEndpoint.KubernetesFunctionDescriptors;
      uploadTooltip = "Upload a Kubernetes descriptor";
      break;

    case DescriptorType.AWS:
      endpoint = ApiDataEndpoint.AwsFunctionDescriptors;
      uploadTooltip = "Upload an AWS descriptor";
      break;
  }

  const theme = useTheme();
  const dispatch = useDispatch();
  const swr = useAuthorizedSWR(endpoint);
  const showDescriptorEditorDialog = useDescriptorEditorDialog();
  const showDescriptorDeleteDialog = useDescriptorDeleteDialog(swr.revalidate);

  return (
    <SwrDataTable
      swr={swr}
      columns={[
        { title: "Name", field: "content.name" },
        { title: "Vendor", field: "content.vendor" },
        { title: "Version", field: "content.version" },
      ]}
      actions={[
        {
          icon: (props) => <Info htmlColor={theme.palette.primary.main} {...props} />,
          tooltip: "Info",
          onClick: (event, descriptor: Descriptor) =>
            dispatch(showDescriptorInfoDialog(descriptor)),
        },
        {
          icon: (props) => <Edit htmlColor={theme.palette.success.main} {...props} />,
          tooltip: "Edit",
          onClick: (event, descriptor: Descriptor) => showDescriptorEditorDialog(descriptor),
        },
        {
          icon: (props) => <DeleteForeverRounded htmlColor={theme.palette.error.main} {...props} />,
          tooltip: "Delete",
          onClick: (event, descriptor: Descriptor) => showDescriptorDeleteDialog(descriptor.id),
        },
        {
          icon: () => (
            <DescriptorUploadButton descriptorType={descriptorType} onUploaded={swr.revalidate} />
          ),
          tooltip: uploadTooltip,
          onClick: null,
          isFreeAction: true,
        },
      ]}
    />
  );
};
