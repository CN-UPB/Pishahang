import { NextPage } from "next";

import UserInfoCard from "../lib/components/content/UserInfoCard";
import { Page } from "../lib/components/layout/Page";

const DashboardPage: NextPage = () => {
  return (
    <Page title="Profile">
      <UserInfoCard></UserInfoCard>
    </Page>
  );
};

export default DashboardPage;
