import { useTheme } from "@material-ui/core";
import React from "react";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { useAuthorizedSWR } from "../../../hooks/useAuthorizedSWR";
import { SwrDataTable } from "../../layout/tables/SwrDataTable";

export const UsersTable: React.FunctionComponent = () => {
  const swr = useAuthorizedSWR(ApiDataEndpoint.Users);

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
    />
  );
};
