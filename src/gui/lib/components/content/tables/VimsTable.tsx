import {
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
import { DeleteForeverRounded, InfoRounded } from "@material-ui/icons";
import React from "react";
import { useDispatch } from "react-redux";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { removeVim } from "../../../api/vims";
import { InjectedAuthorizedSWRProps, withAuthorizedSWR } from "../../../hocs/withAuthorizedSWR";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { useVimsInfoDialog } from "../../../hooks/useVimsInfoDialog";
import { showInfoDialog, showSnackbar } from "../../../store/actions/dialogs";
import { Table } from "../../layout/tables/Table";

type Props = InjectedAuthorizedSWRProps<ApiDataEndpoint.Vims>;

const internalVimsTable: React.FunctionComponent<Props> = ({ data: vims, mutate }) => {
  const theme = useTheme();
  const showVimsInfoDialog = useVimsInfoDialog();
  const dispatch = useDispatch();

  const showShutDownDialog = useGenericConfirmationDialog(
    "Confirm Remove",
    "Are you sure, you want to remove this Vim ?",
    deleteVim,
    "Remove Vim"
  );

  async function deleteVim(confirmed: boolean, id: string) {
    if (confirmed) {
      let reply = await removeVim(id);
      if (reply.success) {
        mutate(
          vims.filter((vim) => vim.vimUuid !== id),
          false
        );
        dispatch(showSnackbar("Plugin successfully stopped"));
      } else {
        dispatch(showInfoDialog({ title: "Error Infomation", message: reply.message }));
      }
    }
  }

  return (
    <TableContainer component={Paper}>
      <Table aria-label="vims table">
        <TableHead>
          <TableRow>
            <TableCell align="center" style={{ width: "20px" }}>
              Name
            </TableCell>
            <TableCell align="center">Uuid</TableCell>

            <TableCell align="center">Cores</TableCell>
            <TableCell align="center">Memory</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {vims.map((Vim) => (
            <TableRow key={Vim.vimUuid}>
              <TableCell align="left">{Vim.vimName}</TableCell>
              <TableCell align="center">{Vim.vimUuid}</TableCell>

              <TableCell align="center">{Vim.coreUsed + "/" + Vim.coreTotal}</TableCell>
              <TableCell align="center">{Vim.memoryUsed + "/" + Vim.memoryTotal}</TableCell>
              <TableCell align="center">
                <Tooltip title="Info" arrow>
                  <IconButton color="primary" onClick={() => showVimsInfoDialog(Vim)}>
                    <InfoRounded />
                  </IconButton>
                </Tooltip>

                <Tooltip title={"Remove " + Vim.vimName} arrow>
                  <IconButton color="secondary" onClick={() => showShutDownDialog(Vim.vimUuid)}>
                    <DeleteForeverRounded />
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

export const VimsTable = withAuthorizedSWR(ApiDataEndpoint.Vims)(internalVimsTable);
