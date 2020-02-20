import { IconButton } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { HighlightOff as Delete, Info as InfoIcon, PlayCircleOutline } from "@material-ui/icons";
import React from "react";

import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useServiceInfoDialog } from "../../../hooks/useServiceInfoDialog";
import { Service } from "../../../models/Service";
import { Vims } from "../../../models/Vims";

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

type Props = {
  /**
   * Property to check page name
   */
  pageName?: any;
  data: Vims[];
};

export const VimsTable: React.FunctionComponent<Props> = props => {
  const classes = useStyles({});
  const theme = useTheme();
  const showServiceInfoDialog = useServiceInfoDialog();
  const showDescriptorDeleteDialog = useDescriptorDeleteDialog();

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Uuid</TableCell>
            <TableCell align="center" style={{ width: "20px" }}>
              Vendor
            </TableCell>
            <TableCell align="center">Cores</TableCell>
            <TableCell align="center">Memory</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {props.data.map(row => (
            <TableRow key={row.uuid}>
              <TableCell component="th" scope="row">
                {row.uuid}
              </TableCell>
              <TableCell align="left">{row.vendor}</TableCell>
              <TableCell align="center">{row.cores}</TableCell>
              <TableCell align="center">{row.memory}</TableCell>
              <TableCell align="center">
                <IconButton color="primary">
                  <InfoIcon />
                </IconButton>
                <IconButton>
                  <PlayCircleOutline htmlColor={theme.palette.success.main} />
                </IconButton>
                <IconButton color="primary">
                  <Delete htmlColor={theme.palette.error.main} />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
