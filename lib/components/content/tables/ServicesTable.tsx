import {
  IconButton,
  Paper,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from "@material-ui/core";
import { useTheme } from "@material-ui/core/styles";
import { InfoRounded, PlayCircleOutline } from "@material-ui/icons";
import React from "react";
import { useDispatch } from "react-redux";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { InjectedAuthorizedSWRProps, withAuthorizedSWR } from "../../../hocs/withAuthorizedSWR";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { Service } from "../../../models/Service";
import { showServiceInfoDialog, showSnackbar } from "../../../store/actions/dialogs";
import { formatDate } from "../../../util/time";
import { Table } from "../../layout/tables/Table";

type Props = InjectedAuthorizedSWRProps<ApiDataEndpoint.Services>;

const InternalServicesTable: React.FunctionComponent<Props> = ({ data: services, mutate }) => {
  const theme = useTheme();
  const dispatch = useDispatch();

  function instantiateService() {
    dispatch(showSnackbar("Service instantiation not implemented"));
  }

  return (
    <TableContainer component={Paper}>
      <Table aria-label="service table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center">Vendor</TableCell>
            <TableCell align="center">Version</TableCell>
            <TableCell align="center">Onboarded at</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {services.map((service) => (
            <TableRow key={service.name}>
              <TableCell component="th" scope="row">
                {service.name}
              </TableCell>
              <TableCell align="center">{service.vendor}</TableCell>
              <TableCell align="center">{service.version}</TableCell>
              <TableCell align="center">{formatDate(service.createdAt)}</TableCell>
              <TableCell align="center">
                <Tooltip title="Info" arrow>
                  <IconButton
                    color="primary"
                    onClick={() => dispatch(showServiceInfoDialog(service))}
                  >
                    <InfoRounded />
                  </IconButton>
                </Tooltip>
                <Tooltip title={"Instantiate " + service.name} arrow>
                  <IconButton onClick={() => instantiateService()}>
                    <PlayCircleOutline htmlColor={theme.palette.success.main} />
                  </IconButton>
                </Tooltip>
                {/* <Tooltip title={"Stop " + service.name} arrow>
                  <IconButton
                    color="primary"
                    onClick={() => showServiceStopDialog(service.id, service.name)}
                  >
                    <RadioButtonCheckedRounded htmlColor={theme.palette.error.main} />
                  </IconButton>
                </Tooltip> */}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export const ServicesTable = withAuthorizedSWR(ApiDataEndpoint.Services)(InternalServicesTable);
