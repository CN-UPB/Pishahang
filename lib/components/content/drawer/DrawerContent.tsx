import Divider from "@material-ui/core/Divider";
import List from "@material-ui/core/List";
import {
  Computer,
  Dns,
  Dvr,
  Person,
  PowerSettingsNew,
  Settings,
  WebAsset,
} from "@material-ui/icons";
import * as React from "react";

import { LinkedListItem } from "../../layout/LinkedListItem";

export const DrawerContent: React.FunctionComponent = () => (
  <>
    <Divider />
    <List>
      <LinkedListItem text={"User Profile"} icon={Person} href={"/user"}></LinkedListItem>
      <LinkedListItem text={"Monitor"} icon={Dvr} href={"/monitor"}></LinkedListItem>
    </List>
    <Divider />
    <List>
      <LinkedListItem text={"VIM Settings"} icon={Settings} href={"/vims"}></LinkedListItem>
    </List>
    <Divider />
    <List>
      <LinkedListItem text={"Descriptors"} icon={Dns} href={""}></LinkedListItem>
    </List>
    <Divider />
    <List>
      <LinkedListItem text={"VNFs"} icon={Computer} href={"/descriptors/vms"}></LinkedListItem>
      <LinkedListItem text={"CNFs"} icon={WebAsset} href={"/descriptors/cns"}></LinkedListItem>
      <LinkedListItem text={"FPGAs"} icon={WebAsset} href={"/descriptors/fpga"}></LinkedListItem>
    </List>
    <Divider />
    <List>
      <LinkedListItem text={"Services"} icon={Dns} href={"/services"}></LinkedListItem>
    </List>
    <Divider />
    <List>
      <LinkedListItem text={"Logout"} icon={PowerSettingsNew} href={""}></LinkedListItem>
    </List>
    <Divider />
  </>
);
