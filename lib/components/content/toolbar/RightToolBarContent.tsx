import { IconButton } from "@material-ui/core";
import { PowerSettingsNew as LogoutIcon, Person as PersonIcon } from "@material-ui/icons";
import * as React from "react";
import { useDispatch } from "react-redux";

import { logout } from "../../../store/actions/auth";
import { IconButtonLink } from "../../links/IconButtonLink";

export const RightToolBarContent: React.FunctionComponent<React.HTMLAttributes<
  HTMLDivElement
>> = props => {
  const dispatch = useDispatch();

  return (
    <div {...props}>
      <IconButtonLink color={"inherit"} href="/user">
        <PersonIcon />
      </IconButtonLink>
      <IconButton color={"inherit"} onClick={() => dispatch(logout())}>
        <LogoutIcon />
      </IconButton>
    </div>
  );
};
