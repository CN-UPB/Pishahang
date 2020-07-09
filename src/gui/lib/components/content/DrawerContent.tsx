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
  Group,
  Person,
  ScatterPlotRounded,
  Settings,
  WebAsset,
} from "@material-ui/icons";
import ExpandLess from "@material-ui/icons/ExpandLess";
import ExpandMore from "@material-ui/icons/ExpandMore";
import { useRouter } from "next/router";
import * as React from "react";
import { useSelector } from "react-redux";

import { useToggle } from "../../hooks/useToggle";
import { selectUserIsAdmin } from "../../store/selectors/auth";
import { LinkedListItem } from "../layout/LinkedListItem";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    nestedList: {
      paddingLeft: theme.spacing(2),
    },
  })
);

export const DrawerContent: React.FunctionComponent = () => {
  const classes = useStyles();
  const router = useRouter();
  const isUserAdmin = useSelector(selectUserIsAdmin);

  const [descriptorsExpanded, toggleDescriptorsExpanded] = useToggle(
    router.pathname.startsWith("/descriptors/") &&
      !router.pathname.startsWith("/descriptors/service")
  );

  return (
    <>
      <List>
        <LinkedListItem text={"Dashboard"} icon={Dashboard} href={"/"}></LinkedListItem>
      </List>

      <List>
        <LinkedListItem text={"VIMs"} icon={Settings} href={"/vims"}></LinkedListItem>
      </List>

      <Divider />

      <List>
        <LinkedListItem
          text={"Service Descriptors"}
          icon={AccountTreeRounded}
          href={"/descriptors/service"}
        ></LinkedListItem>
      </List>
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
            text={"OpenStack"}
            icon={Computer}
            href={"/descriptors/openstack"}
          ></LinkedListItem>
          <LinkedListItem
            text={"Kubernetes"}
            icon={WebAsset}
            href={"/descriptors/kubernetes"}
          ></LinkedListItem>
          <LinkedListItem text={"AWS"} icon={WebAsset} href={"/descriptors/aws"}></LinkedListItem>
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

      <List>
        <LinkedListItem text={"Monitoring"} icon={Dvr} href={"/monitor"}></LinkedListItem>
      </List>

      <Divider />
      <List>
        {isUserAdmin ? (
          <LinkedListItem text={"Users"} icon={Group} href={"/users"}></LinkedListItem>
        ) : (
          ""
        )}
      </List>
      <Divider />
    </>
  );
};
