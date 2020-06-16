import { createStyles, makeStyles, useTheme } from "@material-ui/core/styles";
import { DeleteForeverRounded } from "@material-ui/icons";
import * as React from "react";

import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { ServiceInstance } from "../../../models/ServiceInstance";
import { useThunkDispatch } from "../../../store";
import { terminateServiceInstance } from "../../../store/thunks/services";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";
import { ServiceInstanceStatusField } from "./fields/ServiceInstanceStatusField";

type Props = {
  /**
   * The id of the service to list the instances of
   */
  serviceId: string;
};

const useStyles = makeStyles((theme) =>
  createStyles({
    container: {
      paddingLeft: 42,
      backgroundColor: theme.palette.action.hover,
    },
  })
);

export const ServiceInstancesTable: React.FunctionComponent<Props> = ({ serviceId }) => {
  const theme = useTheme();
  const classes = useStyles();
  const dispatch = useThunkDispatch();

  const swr = useAuthorizedSWR<ServiceInstance[]>(`services/${serviceId}/instances`, {
    refreshInterval: 3000,
  });

  const terminate = async (instanceId: string) => {
    const reply = await dispatch(terminateServiceInstance(serviceId, instanceId));
    if (reply.success) {
      swr.revalidate();
    }
  };

  return (
    <SwrDataTable
      swr={swr}
      columns={[
        { title: "Created at", field: "createdAt", type: "datetime", defaultSort: "desc" },
        {
          title: "Status",
          field: "status",
          render: (instance) => <ServiceInstanceStatusField instance={instance} />,
        },
      ]}
      actions={[
        {
          tooltip: "Terminate instance",
          icon: (props) => (
            <DeleteForeverRounded htmlColor={theme.palette.secondary.main} {...props} />
          ),
          onClick: (event, instance: ServiceInstance) => terminate(instance.id),
        },
      ]}
      components={{
        Container: (props) => <div {...props} className={classes.container}></div>,
      }}
      options={{
        toolbar: false,
        headerStyle: { backgroundColor: "transparent" },
        padding: "dense",
      }}
    />
  );
};
