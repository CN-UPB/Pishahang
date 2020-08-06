import { Add, DeleteForeverRounded, Edit } from "@material-ui/icons";
import * as React from "react";
import { useSelector } from "react-redux";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { useGenericConfirmationDialog } from "../../../hooks/genericConfirmationDialog";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { useStateRef } from "../../../hooks/useStateRef";
import { useUserDialog } from "../../../hooks/useUserDialog";
import { User } from "../../../models/User";
import { useThunkDispatch } from "../../../store";
import { selectUserId } from "../../../store/selectors/auth";
import { addUser, deleteUser, updateUser } from "../../../store/thunks/users";
import theme from "../../../theme";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";

export const UsersTable: React.FunctionComponent = () => {
  const dispatch = useThunkDispatch();
  const swr = useAuthorizedSWR(ApiDataEndpoint.Users);
  const [currentlyEditedUser, setCurrentlyEditedUser, currentlyEditedUserRef] = useStateRef<User>();
  const currentUserId = useSelector(selectUserId);

  const showDeleteUserDialog = useGenericConfirmationDialog(
    "Delete User?",
    "Are you sure you want to delete this user?",
    async (confirmed: boolean, id: string) => {
      if (!confirmed) return;

      let reply = await dispatch(
        deleteUser(id, { successSnackbarMessage: "User successfully deleted" })
      );
      if (reply.success) {
        swr.revalidate();
      }
    },
    "Delete User"
  );

  const showAddUserDialog = useUserDialog(
    "Add User",
    async (user) => {
      const reply = await dispatch(
        addUser(user, { successSnackbarMessage: "User successfully added" })
      );
      if (reply.success) {
        swr.revalidate();
      }
      return reply.success;
    },
    false
  );
  const showEditUserDialog = useUserDialog(
    "Update",
    async (userData) => {
      console.log(userData);
      const reply = await dispatch(updateUser(currentlyEditedUserRef.current.id, userData));
      if (reply.success) {
        swr.revalidate();
      }
      return reply.success;
    },
    false
  );

  return (
    <SwrDataTable
      swr={swr}
      columns={[
        {
          title: "Name",
          render: (user) => user.fullName,
        },
        {
          title: "Username",
          render: (user) => user.username,
        },
        {
          title: "Email",
          render: (user) => user.email,
        },
        {
          title: "User Type",
          render: (user) => (user.isAdmin ? "Administrator" : "Non-Administrator"),
        },
        {
          title: "User Id",
          render: (user) => user.id,
        },
      ]}
      actions={[
        {
          icon: (props) => <Add {...props} />,
          tooltip: "Add User",
          onClick: () => showAddUserDialog(),
          isFreeAction: true,
        },
        (user) => ({
          tooltip: "Edit " + user.username,
          icon: (props) => <Edit htmlColor={theme.palette.success.main} {...props} />,
          onClick: () => {
            setCurrentlyEditedUser(user);
            showEditUserDialog(user);
          },
        }),
        (user) => ({
          disabled: user.id === currentUserId,
          tooltip: user.id === currentUserId ? "" : "Delete " + user.username,
          icon: (props) => (
            <DeleteForeverRounded
              htmlColor={user.id === currentUserId ? theme.palette.grey : theme.palette.error.main}
              {...props}
            />
          ),
          onClick: () => showDeleteUserDialog(user.id),
        }),
      ]}
    />
  );
};
