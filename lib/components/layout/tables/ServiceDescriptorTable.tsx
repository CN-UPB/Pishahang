import { Button, IconButton, Tooltip } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { HighlightOff as Delete, Edit, Info as InfoIcon, QueueRounded } from "@material-ui/icons";
import * as React from "react";

import { onboardServiceDescriptor } from "../../../api/services";
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

async function onBoard(descriptor: Descriptor) {
  console.log(descriptor.id);
  const reply = await onboardServiceDescriptor(descriptor.id);
  alert(JSON.stringify(reply));
}

function instantiateDescriptor(descriptorMeta: Descriptor) {
  console.log(descriptorMeta.id);
}

export const ServiceDescriptorTable: React.FunctionComponent<Props> = props => {
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

            <TableCell>Vendor</TableCell>
            <TableCell>Version</TableCell>
            <TableCell align="center" style={{ width: "300px" }}>
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
              <TableCell>{row.content.vendor}</TableCell>
              <TableCell>{row.content.version}</TableCell>
              <TableCell align="center" style={{ width: "300px" }}>
                <Tooltip title="OnBoard" arrow>
                  <IconButton color="secondary" onClick={() => onBoard(row)}>
                    <QueueRounded />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Info" arrow>
                  <IconButton color="primary" onClick={() => showVnfdInfoDialog(row)}>
                    <InfoIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title={"Edit " + row.content.name} arrow>
                  <IconButton onClick={() => showDescriptorEditorDialog(row)}>
                    <Edit htmlColor={theme.palette.success.main} />
                  </IconButton>
                </Tooltip>

                <Tooltip title={"Delete " + row.content.name} arrow>
                  <IconButton color="primary" onClick={() => showDescriptorDeleteDialog(row.id)}>
                    <Delete htmlColor={theme.palette.error.main} />
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
