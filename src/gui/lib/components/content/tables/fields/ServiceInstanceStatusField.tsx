import { IconButton, LinearProgress, Tooltip } from "@material-ui/core";
import { InfoRounded } from "@material-ui/icons";
import * as React from "react";

import { ServiceInstance } from "../../../../models/ServiceInstance";
import { useThunkDispatch } from "../../../../store";
import { showInfoDialog } from "../../../../store/actions/dialogs";

type Props = {
  /**
   * The service instance to render the status field for
   */
  instance: ServiceInstance;
};

export const ServiceInstanceStatusField: React.FunctionComponent<Props> = ({ instance }) => {
  const status = instance.status;

  const dispatch = useThunkDispatch();

  switch (status) {
    case "INSTANTIATING":
    case "TERMINATING":
      return (
        <div style={{ display: "inline-block" }}>
          {status}
          <LinearProgress />
        </div>
      );

    case "ERROR":
      return (
        <>
          {status}
          <Tooltip title="Show error message" aria-label="show error message">
            <IconButton
              size="small"
              onClick={() =>
                dispatch(showInfoDialog({ title: "Error Information", message: instance.message }))
              }
            >
              <InfoRounded />
            </IconButton>
          </Tooltip>
        </>
      );

    default:
      return <>{status}</>;
  }
};
