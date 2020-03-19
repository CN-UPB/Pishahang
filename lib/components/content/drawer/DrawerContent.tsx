import Collapse from "@material-ui/core/Collapse";
import Divider from "@material-ui/core/Divider";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import { Theme, createStyles, makeStyles } from "@material-ui/core/styles";
import {
  AccountTreeRounded,
  Computer,
  Dashboard,
  Dns,
  Dvr,
  MoneyRounded,
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
        <LinkedListItem
          text={"Dashboard"}
          icon={Dashboard}
          href={"/"} //Unable to add link to Page.tsx for use as Dashboard
        ></LinkedListItem>
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
        <LinkedListItem
          text={"Service Descriptors"}
          icon={AccountTreeRounded}
          href={"/descriptors/services"}
        ></LinkedListItem>
      </List>
      <Divider />
      <List>
        <ListItem button onClick={toggleDescriptorsExpanded}>
          <ListItemIcon>
            <Dns />
          </ListItemIcon>
          <ListItemText primary="Function Descriptors" />
          {descriptorsExpanded ? <ExpandLess /> : <ExpandMore />}
        </ListItem>
      </List>
      <Collapse in={descriptorsExpanded} timeout="auto" unmountOnExit>
        <List component="div" disablePadding className={classes.nestedList}>
          <LinkedListItem
            text={"VM-Based"}
            icon={Computer}
            href={"/descriptors/vms"}
          ></LinkedListItem>
          <LinkedListItem
            text={"CN-Based"}
            icon={WebAsset}
            href={"/descriptors/cns"}
          ></LinkedListItem>
          <LinkedListItem
            text={"FPGA-Based"}
            icon={WebAsset}
            href={"/descriptors/fpga"}
          ></LinkedListItem>
        </List>
      </Collapse>
      <Divider />
      <List>
        <LinkedListItem
          text={"Version Descriptors"}
          icon={MoneyRounded}
          href={"/versiondescriptor"}
        ></LinkedListItem>
      </List>
      <Divider />
      <List>
        <LinkedListItem
          text={"Service Instances"}
          icon={ScatterPlotRounded}
          href={"/services"}
        ></LinkedListItem>
      </List>
      <Divider />
    </>
  );
};
