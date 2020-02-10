import { NextPage } from "next";

import { LoginForm } from "./../lib/components/forms/LoginForm";
import { RegistrationForm } from "./../lib/components/forms/RegistrationForm";
import { Page } from "../lib/components/layout/Page";

const DashboardPage: NextPage = () => {
  return (
    <Page title="Dashboard" hideDrawer hideToolbar>
      <RegistrationForm />
    </Page>
  );
};

export default DashboardPage;
