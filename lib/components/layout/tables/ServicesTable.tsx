import { IconButton, Tooltip } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import {
  HighlightOff as Delete,
  Info as InfoIcon,
  InfoRounded,
  PlayCircleOutline,
} from "@material-ui/icons";
import React from "react";
import { useDispatch } from "react-redux";

import { Service } from "../../../models/Service";
import { showServiceInfoDialog } from "../../../store/actions/dialogs";
import { formatDate } from "../../../util/time";

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

type Props = {
  data: Service[];
};

export const ServicesTable: React.FunctionComponent<Props> = ({ data }) => {
  const classes = useStyles({});
  const theme = useTheme();
  const dispatch = useDispatch();

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
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
          {data.map(service => (
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
                  <IconButton>
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
