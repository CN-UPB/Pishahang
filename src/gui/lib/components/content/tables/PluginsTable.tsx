import { IconButton, Tooltip } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { useTheme } from "@material-ui/core/styles";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import {
  InfoRounded,
  PauseCircleOutlineRounded,
  PlayCircleOutline,
  PowerSettingsNewRounded,
} from "@material-ui/icons";
import React from "react";
import { useDispatch } from "react-redux";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { stopPlugin as apiStopPlugin, changePluginLifecycleState } from "../../../api/plugin";
import { InjectedAuthorizedSWRProps, withAuthorizedSWR } from "../../../hocs/withAuthorizedSWR";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { PluginState } from "../../../models/Plugins";
import { showInfoDialog, showPluginInfoDialog, showSnackbar } from "../../../store/actions/dialogs";
import { updateObjectsListItemById } from "../../../util/swr";
import { Table } from "../../layout/tables/Table";

type Props = InjectedAuthorizedSWRProps<ApiDataEndpoint.Plugins>;

const InternalPluginsTable: React.FunctionComponent<Props> = ({ data: plugins, mutate }) => {
  const theme = useTheme();
  const dispatch = useDispatch();

  const showShutDownDialog = useGenericConfirmationDialog(
    "Confirm Shutdown",
    "Note: This will terminate the plugin's docker container. You cannot restart it from the GUI. " +
      "It may restart automatically though depending on its restart policy.",
    stopPlugin,
    "Shutdown plugin"
  );

  async function manipulatePluginState(id: string, targetState: PluginState) {
    const reply = await changePluginLifecycleState(
      id,
      targetState == PluginState.RUNNING ? "start" : "pause"
    );
    if (reply.success) {
      mutate(
        updateObjectsListItemById(plugins, id, (plugin) => ({ ...plugin, state: targetState })),
        false
      );
    } else {
      dispatch(showInfoDialog({ title: "Error Infomation", message: reply.message }));
    }
  }

  async function stopPlugin(confirmed: boolean, id: string) {
    if (confirmed) {
      let reply = await apiStopPlugin(id);
      if (reply.success) {
        mutate(
          plugins.filter((plugin) => plugin.id !== id),
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
      <Table aria-label="plugins table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center">State</TableCell>
            <TableCell align="center">Version</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {plugins.map((Plugin) => (
            <TableRow key={Plugin.name}>
              <TableCell component="th" scope="row">
                {Plugin.name}
              </TableCell>
              <TableCell align="center">{Plugin.state}</TableCell>
              <TableCell align="center">{Plugin.version}</TableCell>
              <TableCell align="center">
                <Tooltip title="Info" arrow>
                  <IconButton
                    color="primary"
                    onClick={() => dispatch(showPluginInfoDialog(Plugin))}
                  >
                    <InfoRounded />
                  </IconButton>
                </Tooltip>
                {Plugin.state != PluginState.RUNNING && (
                  <Tooltip title={"Run " + Plugin.name} arrow>
                    <IconButton
                      onClick={() => manipulatePluginState(Plugin.id, PluginState.RUNNING)}
                    >
                      <PlayCircleOutline htmlColor={theme.palette.success.main} />
                    </IconButton>
                  </Tooltip>
                )}
                {Plugin.state == PluginState.RUNNING && (
                  <Tooltip title={"Pause " + Plugin.name} arrow>
                    <IconButton
                      color="primary"
                      onClick={() => manipulatePluginState(Plugin.id, PluginState.PAUSED)}
                    >
                      <PauseCircleOutlineRounded />
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title={"Shut down " + Plugin.name} arrow>
                  <IconButton color="secondary" onClick={() => showShutDownDialog(Plugin.id)}>
                    <PowerSettingsNewRounded />
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

export const PluginsTable = withAuthorizedSWR(ApiDataEndpoint.Plugins)(InternalPluginsTable);
