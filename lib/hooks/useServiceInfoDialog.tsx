import {
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
} from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";

import { GenericDialog } from "../components/layout/dialogs/GenericDialog";
import { Service } from "../models/Service";

export function useServiceInfoDialog() {
  let data: Service = null;
  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="vnfdInfo"
      dialogTitle={data.cosd.name}
      open={open}
      onExited={onExited}
      onClose={hideDialog}
      buttons={
        <>
          <Button variant="contained" onClick={hideDialog} color="secondary" autoFocus>
            close
          </Button>
        </>
      }
    >
      <TableContainer component={Paper}>
        <Table aria-label="simple table">
          <TableBody>
            <TableRow key={data.cosd.description}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Description:
                </Typography>
              </TableCell>
              <TableCell align="left">{data.cosd.description}</TableCell>
            </TableRow>

            <TableRow key={data.cosd.descriptor_version}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Descriptor Version:
                </Typography>
              </TableCell>
              <TableCell align="left">{data.cosd.descriptor_version}</TableCell>
            </TableRow>

            <TableRow key={data.cosd.version}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Version:
                </Typography>
              </TableCell>
              <TableCell align="left">{data.cosd.version}</TableCell>
            </TableRow>

            <TableRow key={data.cosd.vendor}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Vendor:
                </Typography>
              </TableCell>
              <TableCell align="left">{data.cosd.vendor}</TableCell>
            </TableRow>

            <TableRow>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Created At:
                </Typography>
              </TableCell>
              <TableCell align="left">{data.created_at.toString()}</TableCell>
            </TableRow>

            <TableRow>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Updated At:
                </Typography>
              </TableCell>
              <TableCell align="left">{data.updated_at.toString()}</TableCell>
            </TableRow>

            <TableRow>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  UUID:
                </Typography>
              </TableCell>
              <TableCell align="left">{data.uuid}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </GenericDialog>
  ));

  return function showServiceInfoDialog(service: Service) {
    data = service;

    showDialog();
  };
}
