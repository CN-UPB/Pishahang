import { NextPage } from "next";

import { LoginForm } from "./../lib/components/forms/LoginForm";
import { Page } from "../lib/components/layout/Page";

const DashboardPage: NextPage = () => {
  return (
    <Page title="Dashboard" hideDrawer hideToolbar>
      <LoginForm />
    </Page>
  );
};

export default DashboardPage;
