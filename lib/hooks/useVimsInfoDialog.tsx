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
import { Vim } from "../models/Vims";
import { useStateRef } from "./useStateRef";

export function useVimsInfoDialog() {
  const [data, setData, dataRef] = useStateRef<Vim>(null);

  const [showDialog, hideDialog] = useModal(({ in: open, onExited }) => (
    <GenericDialog
      dialogId="descriptorInfo"
      dialogTitle={dataRef.current.vimName}
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
            <TableRow key={dataRef.current.vimDomain}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Vim Domain:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.vimDomain}</TableCell>
            </TableRow>

            <TableRow key={dataRef.current.vimCity}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Vim City:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.vimCity}</TableCell>
            </TableRow>

            <TableRow key={dataRef.current.vimEndpoint}>
              <TableCell component="th" scope="row">
                <Typography variant="body2" gutterBottom>
                  Vim Endpoint:
                </Typography>
              </TableCell>
              <TableCell align="left">{dataRef.current.vimEndpoint}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </GenericDialog>
  ));

  return function showVimsInfoDialog(VimsData: Vim) {
    setData(VimsData);
    showDialog();
  };
}
