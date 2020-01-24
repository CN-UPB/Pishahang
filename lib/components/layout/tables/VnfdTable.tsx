import { IconButton } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { HighlightOff as Delete, Edit, Info as InfoIcon } from "@material-ui/icons";
import React from "react";

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

function createData(name: string, vendor: string, status: string) {
  return { name, vendor, status };
}

type Props = {
  /**
   * Property to check page name
   */
  pageName?: any;
};

export const VnfdTable: React.FunctionComponent<Props> = props => {
  const classes = useStyles({});
  const theme = useTheme();

  let rows: any;

  if (props.pageName === "Container") {
    rows = [createData("forwarder-cn-vnf", "eu.sonata-nfv.cloud-service-descriptor", "active")];
  } else {
    rows = [createData("forwarder-vm-vnf", "eu.sonata-nfv.vnf-descriptor", "active")];
  }

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="left">Vendor</TableCell>
            <TableCell align="center" style={{ width: "160px" }}>
              Status
            </TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map(row => (
            <TableRow key={row.name}>
              <TableCell component="th" scope="row">
                {row.name}
              </TableCell>
              <TableCell align="left">{row.vendor}</TableCell>
              <TableCell align="center">{row.status}</TableCell>
              <TableCell align="center">
                <IconButton color="primary">
                  <InfoIcon />
                </IconButton>
                <IconButton>
                  <Edit htmlColor={theme.palette.success.main} />
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
