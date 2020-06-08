import { IconButton, Tooltip, Typography, useTheme } from "@material-ui/core";
import { PowerSettingsNew as LogoutIcon, Person as PersonIcon } from "@material-ui/icons";
import * as React from "react";
import { useDispatch, useSelector } from "react-redux";

import { logout } from "../../store/actions/auth";
import { selectUserFullName } from "../../store/selectors/auth";
import { IconButtonLink } from "../links/IconButtonLink";

export const RightToolbarContent: React.FunctionComponent<React.HTMLAttributes<HTMLDivElement>> = (
  props
) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const userName = useSelector(selectUserFullName);

  return (
    <div {...props}>
      <Typography noWrap style={{ alignSelf: "center", marginRight: theme.spacing(1) }}>
        {userName}
      </Typography>
      <Tooltip title="Profile" arrow>
        <IconButtonLink color={"inherit"} href="/user">
          <PersonIcon />
        </IconButtonLink>
      </Tooltip>
      <Tooltip title="Logout" arrow>
        <IconButton color={"inherit"} onClick={() => dispatch(logout())}>
          <LogoutIcon />
        </IconButton>
      </Tooltip>
    </div>
  );
};
