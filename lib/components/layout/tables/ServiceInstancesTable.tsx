import { IconButton } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { HighlightOff, Info as InfoIcon, PlayCircleOutline, StopRounded } from "@material-ui/icons";
import React from "react";

import { useServiceInfoDialog } from "../../../hooks/useServiceInfoDialog";
import { useServiceStopDialog } from "../../../hooks/useServiceStopDialog";
import { Service } from "../../../models/Service";

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

type Props = {
  data: Service[];
};

export const ServicesTable: React.FunctionComponent<Props> = props => {
  const classes = useStyles({});
  const theme = useTheme();
  const showServiceInfoDialog = useServiceInfoDialog();
  const showServiceStopDialog = useServiceStopDialog();

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center" style={{ width: "20px" }}>
              Vendor
            </TableCell>
            <TableCell align="center">Version</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {props.data.map(service => (
            <TableRow key={service.name}>
              <TableCell component="th" scope="row">
                {service.name}
              </TableCell>
              <TableCell align="center">{service.vendor}</TableCell>
              <TableCell align="center">{service.version}</TableCell>
              <TableCell align="center">
                <IconButton color="primary" onClick={() => showServiceInfoDialog(service)}>
                  <InfoIcon />
                </IconButton>
                <IconButton>
                  <PlayCircleOutline htmlColor={theme.palette.success.main} />
                </IconButton>
                <IconButton
                  color="primary"
                  onClick={() => showServiceStopDialog(service.id, service.name)}
                >
                  <StopRounded htmlColor={theme.palette.error.main} />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
