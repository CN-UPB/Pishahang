import { IconButton, Snackbar, Tooltip } from "@material-ui/core";
import Paper from "@material-ui/core/Paper";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import {
  HighlightOff as Delete,
  Info as InfoIcon,
  InfoRounded,
  PauseCircleOutlineRounded,
  PlayCircleOutline,
  PowerSettingsNewRounded,
  StopRounded,
} from "@material-ui/icons";
import React from "react";
import { useDispatch } from "react-redux";

import { deletePlugin } from "../../../api/plugin";
import { Plugin, PluginState } from "../../../models/Plugins";
import { showInfoDialog, showPluginInfoDialog, showSnackbar } from "../../../store/actions/dialogs";

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

type Props = {
  data: Plugin[];
};

export const PluginsTable: React.FunctionComponent<Props> = ({ data }) => {
  const classes = useStyles({});
  const theme = useTheme();
  const dispatch = useDispatch();

  async function manipulatePluginState(id: string, state: PluginState) {
    dispatch(showSnackbar(id + ": State :" + state));

    // let reply = await deletePlugin(id);
    // if (reply.success) {
    //   dispatch(showSnackbar("Plugin successfully deleted"));
    // } else {
    //   dispatch(showInfoDialog({ title: "Error Infomation", message: reply.message }));
    // }
  }

  function stopPlugin(id: string) {
    dispatch(showSnackbar("Stop" + id));

    // let reply = await deletePlugin(id);
    // if (reply.success) {
    //   dispatch(showSnackbar("Plugin successfully deleted"));
    // } else {
    //   dispatch(showInfoDialog({ title: "Error Infomation", message: reply.message }));
    // }
  }

  function shutDownPlugin(id: string) {
    dispatch(showSnackbar("Shutdown" + id));

    // let reply = await deletePlugin(id);
    // if (reply.success) {
    //   dispatch(showSnackbar("Plugin successfully deleted"));
    // } else {
    //   dispatch(showInfoDialog({ title: "Error Infomation", message: reply.message }));
    // }
  }

  return (
    <TableContainer component={Paper}>
      <Table className={classes.table} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center">State</TableCell>
            <TableCell align="center">Version</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map(Plugin => (
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
                {Plugin.state === PluginState.RUNNING && (
                  <Tooltip title={"Run"} arrow>
                    <IconButton
                      onClick={() => manipulatePluginState(Plugin.id, PluginState.RUNNING)}
                    >
                      <PlayCircleOutline htmlColor={theme.palette.success.main} />
                    </IconButton>
                  </Tooltip>
                )}
                {Plugin.state != PluginState.RUNNING && (
                  <Tooltip title={"Pause"} arrow>
                    <IconButton
                      color="primary"
                      onClick={() => manipulatePluginState(Plugin.id, PluginState.PAUSED)}
                    >
                      <PauseCircleOutlineRounded />
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title={"Stop: " + Plugin.name} arrow>
                  <IconButton color="secondary" onClick={() => stopPlugin(Plugin.id)}>
                    <StopRounded />
                  </IconButton>
                </Tooltip>
                <Tooltip title={"ShutDown: " + Plugin.name} arrow>
                  <IconButton color="secondary" onClick={() => shutDownPlugin(Plugin.id)}>
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
