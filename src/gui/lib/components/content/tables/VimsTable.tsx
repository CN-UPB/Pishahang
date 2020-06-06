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
import { Add, DeleteForeverRounded, InfoRounded } from "@material-ui/icons";
import React from "react";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { InjectedAuthorizedSWRProps, withAuthorizedSWR } from "../../../hocs/withAuthorizedSWR";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { useAddVimDialog } from "../../../hooks/useAddVimDialog";
import { useThunkDispatch } from "../../../store";
import { showVimInfoDialog } from "../../../store/actions/dialogs";
import { deleteVim } from "../../../store/thunks/vims";
import { Table } from "../../layout/tables/Table";

type Props = InjectedAuthorizedSWRProps<ApiDataEndpoint.Vims>;

const InternalVimsTable: React.FunctionComponent<Props> = ({ data: vims, revalidate }) => {
  const dispatch = useThunkDispatch();

  const showRemoveVimDialog = useGenericConfirmationDialog(
    "Remove VIM?",
    "Are you sure, you want to remove this VIM?",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;

      let reply = await dispatch(deleteVim(id, { successSnackbarMessage: "VIM removed" }));
      if (reply.success) {
        revalidate();
      }
    },
    "Remove VIM"
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
