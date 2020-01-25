import { IconButton } from "@material-ui/core";
import { PowerSettingsNew as LogoutIcon, Person as PersonIcon } from "@material-ui/icons";
import * as React from "react";

export const RightToolBarContent: React.FunctionComponent<React.HTMLAttributes<
  HTMLDivElement
>> = props => (
  <div {...props}>
    <IconButton color={"inherit"}>
      <PersonIcon />
    </IconButton>
    <IconButton color={"inherit"}>
      <LogoutIcon />
    </IconButton>
  </div>
);
