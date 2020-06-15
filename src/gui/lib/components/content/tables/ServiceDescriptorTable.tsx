import { useTheme } from "@material-ui/core/styles";
import { DeleteForeverRounded, Edit, Info, QueueRounded } from "@material-ui/icons";
import * as React from "react";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useDescriptorEditorDialog } from "../../../hooks/useDescriptorEditorDialog";
import { Descriptor, DescriptorType } from "../../../models/Descriptor";
import { useThunkDispatch } from "../../../store";
import { showDescriptorInfoDialog, showInfoDialog } from "../../../store/actions/dialogs";
import { onboardServiceDescriptor } from "../../../store/thunks/services";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";
import { DescriptorUploadButton } from "../DescriptorUploadButton";

export const ServiceDescriptorTable: React.FunctionComponent = () => {
  const theme = useTheme();
  const dispatch = useThunkDispatch();
  const swr = useAuthorizedSWR(ApiDataEndpoint.ServiceDescriptors);

  const showDescriptorEditorDialog = useDescriptorEditorDialog();
  const showDescriptorDeleteDialog = useDescriptorDeleteDialog(swr.revalidate);

  async function onboard(descriptorId: string) {
    const reply = await dispatch(onboardServiceDescriptor(descriptorId));
    if (reply.success) {
      dispatch(
        showInfoDialog({
          title: "Success",
          message:
            "The descriptor was successfully onboarded. " +
            'You can find it in the "Services" section now.',
        })
      );
    }
  }

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
          icon: (props) => <QueueRounded htmlColor={theme.palette.secondary.main} {...props} />,
          tooltip: "Onboard",
          onClick: (event, descriptor: Descriptor) => onboard(descriptor.id),
        },
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
            <DescriptorUploadButton
              descriptorType={DescriptorType.Service}
              onUploaded={swr.revalidate}
            />
          ),
          tooltip: "Upload a service descriptor",
          onClick: null,
          isFreeAction: true,
        },
      ]}
    />
  );
};
