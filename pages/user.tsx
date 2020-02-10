import { NextPage } from "next";

import { UserProfile } from "./../lib/components/forms/userprofile";
import { Page } from "../lib/components/layout/Page";

const DashboardPage: NextPage = () => {
  return (
    <Page title="User Profile">
      <UserProfile />
    </Page>
  );
};

export default DashboardPage;
