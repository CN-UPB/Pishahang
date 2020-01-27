import Collapse from "@material-ui/core/Collapse";
import Divider from "@material-ui/core/Divider";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import { Theme, createStyles, makeStyles } from "@material-ui/core/styles";
import {
  Computer,
  Dashboard,
  Dns,
  Dvr,
  ScatterPlotRounded,
  Settings,
  WebAsset,
} from "@material-ui/icons";
import ExpandLess from "@material-ui/icons/ExpandLess";
import ExpandMore from "@material-ui/icons/ExpandMore";
import { useRouter } from "next/router";
import * as React from "react";

import { useToggle } from "../../../hooks/useToggle";
import { LinkedListItem } from "../../layout/LinkedListItem";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    nestedList: {
      paddingLeft: theme.spacing(2),
    },
  })
);

export const DrawerContent: React.FunctionComponent = () => {
  const classes = useStyles({});
  const router = useRouter();

  const [descriptorsExpanded, toggleDescriptorsExpanded] = useToggle(
    router.pathname.startsWith("/descriptors/")
  );

  return (
    <>
      <Divider />
      <List>
        <LinkedListItem text={"Dashboard"} icon={Dashboard} href={""}></LinkedListItem>
      </List>
      <Divider />
      <List>
        <LinkedListItem text={"Monitoring"} icon={Dvr} href={"/monitor"}></LinkedListItem>
      </List>
      <Divider />
      <List>
        <LinkedListItem text={"VIM Settings"} icon={Settings} href={"/vims"}></LinkedListItem>
      </List>
      <Divider />
      <List>
        <ListItem button onClick={toggleDescriptorsExpanded}>
          <ListItemIcon>
            <Dns />
          </ListItemIcon>
          <ListItemText primary="Descriptors" />
          {descriptorsExpanded ? <ExpandLess /> : <ExpandMore />}
        </ListItem>
      </List>
      <Collapse in={descriptorsExpanded} timeout="auto" unmountOnExit>
        <List component="div" disablePadding className={classes.nestedList}>
          <LinkedListItem text={"VNFs"} icon={Computer} href={"/descriptors/vms"}></LinkedListItem>
          <LinkedListItem text={"CNFs"} icon={WebAsset} href={"/descriptors/cns"}></LinkedListItem>
          <LinkedListItem
            text={"FPGAs"}
            icon={WebAsset}
            href={"/descriptors/fpga"}
          ></LinkedListItem>
        </List>
      </Collapse>
      <Divider />
      <List>
        <LinkedListItem
          text={"Services"}
          icon={ScatterPlotRounded}
          href={"/services"}
        ></LinkedListItem>
      </List>
      <Divider />
    </>
  );
};
