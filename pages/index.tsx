import { NextPage } from "next";

import DashBoardGraph from "../lib/components/layout/charts/DashboardGraph";
import { Page } from "../lib/components/layout/Page";

const DashboardPage: NextPage = () => {
  return (
    <Page title="Dashboard">
      <DashBoardGraph></DashBoardGraph>
    </Page>
  );
};

export default DashboardPage;
