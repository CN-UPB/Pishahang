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

import { ApiDataEndpoint } from "../../../api/endpoints";
import { InjectedAuthorizedSWRProps, withAuthorizedSWR } from "../../../hocs/withAuthorizedSWR";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { PluginState } from "../../../models/Plugin";
import { useThunkDispatch } from "../../../store";
import { showPluginInfoDialog } from "../../../store/actions/dialogs";
import { changePluginLifecycleState, stopPlugin } from "../../../store/thunks/plugins";
import { updateObjectsListItemById } from "../../../util/swr";
import { Table } from "../../layout/tables/Table";

type Props = InjectedAuthorizedSWRProps<ApiDataEndpoint.Plugins>;

const InternalPluginsTable: React.FunctionComponent<Props> = ({
  data: plugins,
  mutate,
  revalidate,
}) => {
  const theme = useTheme();
  const dispatch = useThunkDispatch();

  const showShutdownDialog = useGenericConfirmationDialog(
    "Confirm Shutdown",
    "This will terminate the plugin's docker container. You cannot restart it from the GUI. " +
      "It may restart automatically though depending on the container's restart policy.",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;
      let reply = await dispatch(
        stopPlugin(id, { successSnackbarMessage: "Plugin successfully stopped" })
      );
      if (reply.success) {
        revalidate();
      }
    },
    "Shutdown plugin"
  );

  const manipulatePluginState = async (id: string, targetState: PluginState) => {
    const reply = await dispatch(changePluginLifecycleState(id, targetState));
    if (reply.success) {
      mutate(
        updateObjectsListItemById(plugins, id, (plugin) => ({ ...plugin, state: targetState })),
        false
      );
    }
  };

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
          {plugins.map((plugin) => (
            <TableRow key={plugin.name}>
              <TableCell component="th" scope="row">
                {plugin.name}
              </TableCell>
              <TableCell align="center">{plugin.state}</TableCell>
              <TableCell align="center">{plugin.version}</TableCell>
              <TableCell align="center">
                <Tooltip title="Info" arrow>
                  <IconButton
                    color="primary"
                    onClick={() => dispatch(showPluginInfoDialog(plugin))}
                  >
                    <InfoRounded />
                  </IconButton>
                </Tooltip>
                {plugin.state != PluginState.RUNNING && (
                  <Tooltip title={"Run " + plugin.name} arrow>
                    <IconButton
                      onClick={() => manipulatePluginState(plugin.id, PluginState.RUNNING)}
                    >
                      <PlayCircleOutline htmlColor={theme.palette.success.main} />
                    </IconButton>
                  </Tooltip>
                )}
                {plugin.state == PluginState.RUNNING && (
                  <Tooltip title={"Pause " + plugin.name} arrow>
                    <IconButton
                      color="primary"
                      onClick={() => manipulatePluginState(plugin.id, PluginState.PAUSED)}
                    >
                      <PauseCircleOutlineRounded />
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title={"Shut down " + plugin.name} arrow>
                  <IconButton color="secondary" onClick={() => showShutdownDialog(plugin.id)}>
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
