import { useTheme } from "@material-ui/core/styles";
import { InfoRounded, PlayCircleOutline } from "@material-ui/icons";
import * as React from "react";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { Service } from "../../../models/Service";
import { useThunkDispatch } from "../../../store";
import { showServiceInfoDialog } from "../../../store/actions/dialogs";
import { instantiateService } from "../../../store/thunks/services";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";

export const ServicesTable: React.FunctionComponent = () => {
  const theme = useTheme();
  const dispatch = useThunkDispatch();
  const swr = useAuthorizedSWR(ApiDataEndpoint.Services);

  const instantiate = async (id: string) => {
    const reply = await dispatch(
      instantiateService(id, { successSnackbarMessage: "Instantiation request made" })
    );
  };

  return (
    <SwrDataTable
      swr={swr}
      title="Services"
      columns={[
        { title: "Name", field: "name" },
        { title: "Vendor", field: "vendor" },
        { title: "Version", field: "version" },
        { title: "Onboarded at", field: "createdAt", type: "datetime" },
      ]}
      actions={[
        {
          icon: (props) => <InfoRounded htmlColor={theme.palette.primary.main} {...props} />,
          tooltip: "Info",
          onClick: (event, service: Service) => dispatch(showServiceInfoDialog(service)),
        },
        {
          icon: (props) => <PlayCircleOutline htmlColor={theme.palette.success.main} {...props} />,
          tooltip: "Instantiate",
          onClick: (event, service: Service) => instantiate(service.id),
        },
      ]}
    />
  );
};
