import { NextPage } from "next";

import { UsersTable } from "../lib/components/content/tables/UsersTable";
import { Page } from "../lib/components/layout/Page";

const DashboardPage: NextPage = () => {
  return (
    <Page title="Users">
      <UsersTable></UsersTable>
    </Page>
  );
};

export default DashboardPage;
