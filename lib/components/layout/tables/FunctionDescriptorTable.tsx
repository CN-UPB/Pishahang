import { Button, IconButton } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { HighlightOff as Delete, Edit, Info as InfoIcon } from "@material-ui/icons";
import * as React from "react";

import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useDescriptorEditorDialog } from "../../../hooks/useDescriptorEditorDialog";
import { useDescriptorInfoDialog } from "../../../hooks/useDescriptorInfoDialog";
import { Descriptor } from "../../../models/Descriptor";

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
  data: Descriptor[];
};

function onBoard(descriptorMeta: Descriptor) {
  console.log(descriptorMeta.id);
}

function instantiateDescriptor(descriptorMeta: Descriptor) {
  console.log(descriptorMeta.id);
}

export const FunctionDescriptorTable: React.FunctionComponent<Props> = props => {
  const classes = useStyles({});
  const theme = useTheme();
  const showVnfdInfoDialog = useDescriptorInfoDialog();
  const showDescriptorEditorDialog = useDescriptorEditorDialog();
  const showDescriptorDeleteDialog = useDescriptorDeleteDialog();

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Vendor
            </TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Version
            </TableCell>
            <TableCell align="center" style={{ width: "400px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {props.data.map(row => (
            <TableRow key={row.content.name}>
              <TableCell component="th" scope="row">
                {row.content.name}
              </TableCell>
              <TableCell align="center" style={{ width: "200px" }}>
                {row.content.vendor}
              </TableCell>
              <TableCell align="center" style={{ width: "200px" }}>
                {row.content.version}
              </TableCell>
              <TableCell align="center" style={{ width: "400px" }}>
                <IconButton color="primary" onClick={() => showVnfdInfoDialog(row)}>
                  <InfoIcon />
                </IconButton>
                <IconButton onClick={() => showDescriptorEditorDialog(row)}>
                  <Edit htmlColor={theme.palette.success.main} />
                </IconButton>
                <IconButton color="primary" onClick={() => showDescriptorDeleteDialog(row.id)}>
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
