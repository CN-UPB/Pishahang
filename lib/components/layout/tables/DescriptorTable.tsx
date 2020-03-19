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
import React from "react";

import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useDescriptorEditorDialog } from "../../../hooks/useDescriptorEditorDialog";
import { useVnfdInfoDialog } from "../../../hooks/useVnfdInfoDialog";
import { DescriptorMeta } from "../../../models/DescriptorMeta";

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
  data: DescriptorMeta[];
};

function onBoard(descriptorMeta: DescriptorMeta) {
  console.log(descriptorMeta.id);
}

function instantiateDescriptor(descriptorMeta: DescriptorMeta) {
  console.log(descriptorMeta.id);
}

export const DescriptorTable: React.FunctionComponent<Props> = props => {
  const classes = useStyles({});
  const theme = useTheme();
  const showVnfdInfoDialog = useVnfdInfoDialog();
  const showDescriptorEditorDialog = useDescriptorEditorDialog();
  const showDescriptorDeleteDialog = useDescriptorDeleteDialog();

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>

            <TableCell align="center" style={{ width: "160px" }}>
              Status
            </TableCell>
            <TableCell align="center">Options</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {props.data.map(row => (
            <TableRow key={row.descriptor.name}>
              <TableCell component="th" scope="row">
                {row.descriptor.name}
              </TableCell>
              <TableCell align="center">{"UPLOADED"}</TableCell>
              <TableCell align="center">
                <Button
                  variant="outlined"
                  color="secondary"
                  style={{ marginRight: "2px" }}
                  onClick={() => onBoard(row)}
                >
                  OnBoard
                </Button>

                {/* </TableCell>
              <TableCell> */}

                <Button
                  variant="outlined"
                  color="primary"
                  style={{ marginLeft: "2px" }}
                  onClick={() => instantiateDescriptor(row)}
                >
                  Instantiate
                </Button>
              </TableCell>
              <TableCell align="center">
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
