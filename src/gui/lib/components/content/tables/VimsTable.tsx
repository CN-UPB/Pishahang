import {
  Fab,
  IconButton,
  Paper,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from "@material-ui/core";
import { useTheme } from "@material-ui/core/styles";
import { Add, DeleteForeverRounded, InfoRounded } from "@material-ui/icons";
import React from "react";
import { useDispatch } from "react-redux";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { deleteVim } from "../../../api/vims";
import { InjectedAuthorizedSWRProps, withAuthorizedSWR } from "../../../hocs/withAuthorizedSWR";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { useAddVimDialog } from "../../../hooks/useAddVimDialog";
import { showInfoDialog, showSnackbar, showVimInfoDialog } from "../../../store/actions/dialogs";
import { Table } from "../../layout/tables/Table";

type Props = InjectedAuthorizedSWRProps<ApiDataEndpoint.Vims>;

const InternalVimsTable: React.FunctionComponent<Props> = ({ data: vims, mutate, revalidate }) => {
  const theme = useTheme();
  const dispatch = useDispatch();

  const showRemoveVimDialog = useGenericConfirmationDialog(
    "Confirm Remove",
    "Are you sure, you want to remove this VIM?",
    async (confirmed: boolean, id: string) => {
      if (confirmed) {
        let reply = await deleteVim(id);
        if (reply.success) {
          mutate(
            vims.filter((vim) => vim.id !== id),
            false
          );
          dispatch(showSnackbar("VIM removed"));
        } else {
          dispatch(showInfoDialog({ title: "Error Removing VIM", message: reply.message }));
        }
      }
    },
    "Remove Vim"
  );

  const showAddVimDialog = useAddVimDialog(revalidate);

  return (
    <>
      <Tooltip title="Add a VIM" arrow>
        <Fab
          color="primary"
          size="small"
          style={{ float: "right" }}
          aria-label="Add a virtual infrastructure manager"
          onClick={showAddVimDialog}
        >
          <Add />
        </Fab>
      </Tooltip>
      <TableContainer component={Paper}>
        <Table aria-label="Virtual Infrastructure Managers">
          <TableHead>
            <TableRow>
              <TableCell align="left">Name</TableCell>
              <TableCell align="center">Country</TableCell>
              <TableCell align="center">City</TableCell>
              <TableCell align="center">Core Usage</TableCell>
              <TableCell align="center">Memory Usage</TableCell>
              <TableCell align="center" style={{ width: "200px" }}>
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {vims.map((vim) => (
              <TableRow key={vim.id}>
                <TableCell align="left">{vim.name}</TableCell>
                <TableCell align="center">{vim.country}</TableCell>
                <TableCell align="center">{vim.city}</TableCell>
                <TableCell align="center">{vim.coresUsed + "/" + vim.coresTotal}</TableCell>
                <TableCell align="center">{vim.memoryUsed + "/" + vim.memoryTotal}</TableCell>
                <TableCell align="center">
                  <Tooltip title="Info" arrow>
                    <IconButton color="primary" onClick={() => dispatch(showVimInfoDialog(vim))}>
                      <InfoRounded />
                    </IconButton>
                  </Tooltip>

                  <Tooltip title={"Remove " + vim.name} arrow>
                    <IconButton color="secondary" onClick={() => showRemoveVimDialog(vim.id)}>
                      <DeleteForeverRounded />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
};

export const VimsTable = withAuthorizedSWR(ApiDataEndpoint.Vims)(InternalVimsTable);
