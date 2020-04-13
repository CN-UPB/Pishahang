import { Fab, Tooltip } from "@material-ui/core";
import { Add } from "@material-ui/icons";
import { NextPage } from "next";

import { Page } from "../lib/components/layout/Page";
import { useAddUserDialog } from "../lib/hooks/useAddUserDialog";

const DashboardPage: NextPage = () => {
  const showUserProfileDialog = useAddUserDialog();
  return (
    <Page title="User Profile">
      <Tooltip title="Add User" arrow>
        <Fab
          color="primary"
          size="small"
          style={{ float: "right" }}
          aria-label="Add"
          onClick={() => showUserProfileDialog()}
        >
          <Add />
        </Fab>
      </Tooltip>
    </Page>
  );
};

export default DashboardPage;
