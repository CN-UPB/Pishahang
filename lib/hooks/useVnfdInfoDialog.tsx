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
import { DescriptorMeta } from "../models/DescriptorMeta";
import { useStateRef } from "./useStateRef";

export function useVnfdInfoDialog() {
  const [data, setData, dataRef] = useStateRef<DescriptorMeta>(null);

  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="descriptorInfo"
      dialogTitle={dataRef.current.descriptor.name}
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
            <TableRow key={dataRef.current.descriptor.description}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Description:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.descriptor.description}</TableCell>
            </TableRow>

            <TableRow key={dataRef.current.descriptor.descriptor_version}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Descriptor Version:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.descriptor.descriptor_version}</TableCell>
            </TableRow>

            <TableRow key={dataRef.current.descriptor.version}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Version:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.descriptor.version}</TableCell>
            </TableRow>

            <TableRow key={dataRef.current.descriptor.vendor}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Vendor:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.descriptor.vendor}</TableCell>
            </TableRow>

            <TableRow>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Created At:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.createdAt}</TableCell>
            </TableRow>

            <TableRow>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Updated At:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.updatedAt}</TableCell>
            </TableRow>

            <TableRow>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  UUID:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.id}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </GenericDialog>
  ));

  return function showVnfdInfoDialog(descriptorMeta: DescriptorMeta) {
    setData(descriptorMeta);
    showDialog();
  };
}
