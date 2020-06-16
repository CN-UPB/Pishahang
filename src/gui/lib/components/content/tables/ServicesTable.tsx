import { useTheme } from "@material-ui/core/styles";
import { DeleteForeverRounded, InfoRounded, PlayCircleOutline } from "@material-ui/icons";
import * as React from "react";
import { mutate } from "swr";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { Service } from "../../../models/Service";
import { useThunkDispatch } from "../../../store";
import { showServiceInfoDialog } from "../../../store/actions/dialogs";
import { deleteService, instantiateService } from "../../../store/thunks/services";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";
import { ServiceInstancesTable } from "./ServiceInstancesTable";

export const ServicesTable: React.FunctionComponent = () => {
  const theme = useTheme();
  const dispatch = useThunkDispatch();
  const swr = useAuthorizedSWR(ApiDataEndpoint.Services, { revalidateOnFocus: false });

  const instantiate = async (id: string) => {
    const reply = await dispatch(instantiateService(id));
    if (reply.success) {
      // Trigger SWR revalidation of instances to update the corresponding table
      mutate(`services/${id}/instances`);
    }
  };

  const showDeleteDialog = useGenericConfirmationDialog(
    "Delete service?",
    "This will delete the onboarded snapshots of the descriptors used by this service.",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;
      let reply = await dispatch(deleteService(id));
      if (reply.success) {
        swr.revalidate();
      }
    },
    "Delete service"
  );

  return (
    <SwrDataTable
      swr={swr}
      columns={[
        { title: "Name", field: "name" },
        { title: "Vendor", field: "vendor" },
        { title: "Version", field: "version" },
        { title: "Onboarded at", field: "createdAt", type: "datetime", defaultSort: "desc" },
      ]}
      actions={[
        {
          icon: (props) => <InfoRounded htmlColor={theme.palette.primary.main} {...props} />,
          tooltip: "Info",
          onClick: (event, service: Service) => dispatch(showServiceInfoDialog(service)),
        },
        (service) => ({
          tooltip: "Instantiate " + service.name,
          icon: (props) => <PlayCircleOutline htmlColor={theme.palette.success.main} {...props} />,
          onClick: (event, service: Service) => instantiate(service.id),
        }),
        (service) => ({
          tooltip: "Delete " + service.name,
          icon: (props) => (
            <DeleteForeverRounded htmlColor={theme.palette.secondary.main} {...props} />
          ),
          onClick: () => showDeleteDialog(service.id),
        }),
      ]}
      detailPanel={[
        {
          tooltip: "Show instances",
          render: (service) => <ServiceInstancesTable serviceId={service.id} />,
        },
      ]}
      onRowClick={(event, service, togglePanel) => togglePanel()}
    />
  );
};
