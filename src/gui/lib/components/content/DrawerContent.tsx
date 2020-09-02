import { Collapse, Divider, List, ListItem, ListItemIcon, ListItemText } from "@material-ui/core";
import { Theme, createStyles, makeStyles } from "@material-ui/core/styles";
import {
  AccountTreeRounded,
  Computer,
  Dashboard,
  Dns,
  Dvr,
  ExpandLess,
  ExpandMore,
  Group,
  ScatterPlotRounded,
  Settings,
  WebAsset,
} from "@material-ui/icons";
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
        <LinkedListItem text={"Dashboard"} icon={Dashboard} href={"/"} />
        {isUserAdmin && <LinkedListItem text={"VIMs"} icon={Settings} href={"/vims"} />}
      </List>

      <Divider />

      <List>
        <LinkedListItem
          text={"Service Descriptors"}
          icon={AccountTreeRounded}
          href={"/descriptors/service"}
        />
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
          <LinkedListItem text={"OpenStack"} icon={Computer} href={"/descriptors/openstack"} />
          <LinkedListItem text={"Kubernetes"} icon={WebAsset} href={"/descriptors/kubernetes"} />
          <LinkedListItem text={"AWS"} icon={WebAsset} href={"/descriptors/aws"} />
        </List>
      </Collapse>

      <Divider />

      <List>
        <LinkedListItem text={"Services"} icon={ScatterPlotRounded} href={"/services"} />

        {isUserAdmin && <LinkedListItem text={"Plugins"} icon={Dvr} href={"/monitor"} />}
      </List>

      <Divider />
      {isUserAdmin && (
        <>
          <List>
            <LinkedListItem text={"Users"} icon={Group} href={"/users"} />
          </List>
          <Divider />
        </>
      )}
    </>
  );
};
