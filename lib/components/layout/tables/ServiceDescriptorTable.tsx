import { Button, IconButton, Tooltip } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { DeleteForeverRounded, Edit, Info as InfoIcon, QueueRounded } from "@material-ui/icons";
import * as React from "react";
import { useDispatch } from "react-redux";

import { onboardServiceDescriptor } from "../../../api/services";
import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useDescriptorEditorDialog } from "../../../hooks/useDescriptorEditorDialog";
import { Descriptor } from "../../../models/Descriptor";
import { showDescriptorInfoDialog } from "../../../store/actions/dialogs";

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

type Props = {
  data: Descriptor[];
};

async function onboard(descriptor: Descriptor) {
  console.log(descriptor.id);
  const reply = await onboardServiceDescriptor(descriptor.id);
  alert(JSON.stringify(reply));
}

export const ServiceDescriptorTable: React.FunctionComponent<Props> = ({ data }) => {
  const classes = useStyles({});
  const theme = useTheme();
  const dispatch = useDispatch();
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
          {data.map(descriptor => (
            <TableRow key={descriptor.content.name}>
              <TableCell component="th" scope="row">
                {descriptor.content.name}
              </TableCell>
              <TableCell>{descriptor.content.vendor}</TableCell>
              <TableCell>{descriptor.content.version}</TableCell>
              <TableCell align="center" style={{ width: "300px" }}>
                <Tooltip title={"Onboard " + descriptor.content.name} arrow>
                  <IconButton color="secondary" onClick={() => onboard(descriptor)}>
                    <QueueRounded />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Info" arrow>
                  <IconButton
                    color="primary"
                    onClick={() => dispatch(showDescriptorInfoDialog(descriptor))}
                  >
                    <InfoIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title={"Edit " + descriptor.content.name} arrow>
                  <IconButton onClick={() => showDescriptorEditorDialog(descriptor)}>
                    <Edit htmlColor={theme.palette.success.main} />
                  </IconButton>
                </Tooltip>

                <Tooltip title={"Delete " + descriptor.content.name} arrow>
                  <IconButton
                    color="primary"
                    onClick={() => showDescriptorDeleteDialog(descriptor.id)}
                  >
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
