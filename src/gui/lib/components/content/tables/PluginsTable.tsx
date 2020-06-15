import { useTheme } from "@material-ui/core/styles";
import {
  Info,
  PauseCircleOutlineRounded,
  PlayCircleOutline,
  PowerSettingsNewRounded,
} from "@material-ui/icons";
import React from "react";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { Plugin, PluginState } from "../../../models/Plugin";
import { useThunkDispatch } from "../../../store";
import { showPluginInfoDialog } from "../../../store/actions/dialogs";
import { changePluginLifecycleState, stopPlugin } from "../../../store/thunks/plugins";
import { updateObjectsListItemById } from "../../../util/swr";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";

export const PluginsTable: React.FunctionComponent = () => {
  const theme = useTheme();
  const dispatch = useThunkDispatch();
  const swr = useAuthorizedSWR(ApiDataEndpoint.Plugins);

  const showShutdownDialog = useGenericConfirmationDialog(
    "Confirm Shutdown",
    "This will terminate the plugin's Docker container. You cannot restart it from the GUI. " +
      "It may restart automatically though, depending on the container's restart policy.",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;
      let reply = await dispatch(
        stopPlugin(id, { successSnackbarMessage: "Plugin successfully stopped" })
      );
      if (reply.success) {
        swr.revalidate();
      }
    },
    "Shutdown plugin"
  );

  const manipulatePluginState = async (id: string, targetState: PluginState) => {
    const reply = await dispatch(changePluginLifecycleState(id, targetState));
    if (reply.success) {
      swr.mutate(
        updateObjectsListItemById(swr.data, id, (plugin) => ({ ...plugin, state: targetState })),
        false
      );
    }
  };

  return (
    <SwrDataTable
      swr={swr}
      columns={[
        { title: "Name", field: "name" },
        { title: "Version", field: "version" },
        { title: "State", field: "state" },
      ]}
      actions={[
        {
          icon: (props) => <Info htmlColor={theme.palette.primary.main} {...props} />,
          tooltip: "Info",
          onClick: (event, plugin: Plugin) => dispatch(showPluginInfoDialog(plugin)),
        },
        (plugin) => ({
          tooltip: "Run " + plugin.name,
          hidden: plugin.state === PluginState.RUNNING,
          icon: (props) => <PlayCircleOutline htmlColor={theme.palette.success.main} {...props} />,
          onClick: () => manipulatePluginState(plugin.id, PluginState.RUNNING),
        }),
        (plugin) => ({
          tooltip: "Pause " + plugin.name,
          hidden: plugin.state !== PluginState.RUNNING,
          icon: (props) => (
            <PauseCircleOutlineRounded htmlColor={theme.palette.primary.main} {...props} />
          ),
          onClick: () => manipulatePluginState(plugin.id, PluginState.PAUSED),
        }),
        (plugin) => ({
          tooltip: "Shut down " + plugin.name,
          icon: (props) => (
            <PowerSettingsNewRounded htmlColor={theme.palette.secondary.main} {...props} />
          ),
          onClick: () => showShutdownDialog(plugin.id),
        }),
      ]}
    />
  );
};
