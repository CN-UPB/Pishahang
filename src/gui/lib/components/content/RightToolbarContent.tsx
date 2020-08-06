import { IconButton, Tooltip, Typography, useTheme } from "@material-ui/core";
import { PowerSettingsNew as LogoutIcon, Person as PersonIcon } from "@material-ui/icons";
import * as React from "react";
import { useDispatch, useSelector } from "react-redux";

import { useUserDialog } from "../../hooks/useUserDialog";
import { useThunkDispatch } from "../../store";
import { logout } from "../../store/actions/auth";
import { selectUser, selectUserFullName } from "../../store/selectors/auth";
import { fetchUser } from "../../store/thunks/auth";
import { updateUser } from "../../store/thunks/users";
import { UserForm } from "../forms/UserForm";
import { IconButtonLink } from "../links/IconButtonLink";

export const RightToolbarContent: React.FunctionComponent<React.HTMLAttributes<HTMLDivElement>> = (
  props
) => {
  const theme = useTheme();
  const dispatch = useThunkDispatch();
  const user = useSelector(selectUser);

  const showEditUserDialog = useUserDialog(
    "Update",
    async (userData) => {
      const reply = await dispatch(updateUser(user.id, userData));
      if (reply.success) {
        fetchUser();
      }
      return reply.success;
    },
    true
  );

  return (
    <div {...props}>
      <Typography noWrap style={{ alignSelf: "center", marginRight: theme.spacing(1) }}>
        {user && user.username}
      </Typography>
      <Tooltip title="Profile" arrow>
        <IconButton color={"inherit"} onClick={() => showEditUserDialog(user)}>
          <PersonIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Logout" arrow>
        <IconButton color={"inherit"} onClick={() => dispatch(logout())}>
          <LogoutIcon />
        </IconButton>
      </Tooltip>
    </div>
  );
};
