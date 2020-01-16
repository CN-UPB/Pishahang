import Divider from "@material-ui/core/Divider";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import { Computer, Dns, Dock, Dvr, Person, PowerSettingsNew, WebAsset } from "@material-ui/icons";
import MailIcon from "@material-ui/icons/Mail";
import InboxIcon from "@material-ui/icons/MoveToInbox";
import * as React from "react";

import { LinkedListItem } from "../../layout/LinkedListItem";

export const DrawerContent: React.FunctionComponent = () => (
  <>
    <Divider />
    <List>
      <LinkedListItem text={"User Profile"} icon={Person} href={""}></LinkedListItem>
      <LinkedListItem text={"Monitor"} icon={Dvr} href={""}></LinkedListItem>
    </List>
    <Divider />
    <List>
      <LinkedListItem text={"Services"} icon={Dns} href={""}></LinkedListItem>
      <LinkedListItem text={"Virtual Machines"} icon={Computer} href={""}></LinkedListItem>
      <LinkedListItem text={"Containers"} icon={WebAsset} href={""}></LinkedListItem>
    </List>
    <Divider />
    <List>
      <LinkedListItem text={"Logout"} icon={PowerSettingsNew} href={""}></LinkedListItem>
    </List>
    <Divider />
  </>
);
