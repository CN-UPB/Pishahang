import { IconButton, Tooltip } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { DeleteForeverRounded, InfoRounded } from "@material-ui/icons";
import React from "react";

import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useVimsInfoDialog } from "../../../hooks/useVimsInfoDialog";
import { Vim } from "../../../models/Vims";

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
  data: Vim[];
};

export const VimsTable: React.FunctionComponent<Props> = props => {
  const classes = useStyles({});
  const theme = useTheme();
  const showVimsInfoDialog = useVimsInfoDialog();
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
                <Tooltip title="Info" arrow>
                  <IconButton color="primary" onClick={() => showVimsInfoDialog(row)}>
                    <InfoRounded />
                  </IconButton>
                </Tooltip>

                <Tooltip title={"Delete " + row.vimName} arrow>
                  <IconButton color="primary">
                    <DeleteForeverRounded htmlColor={theme.palette.error.main} />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
