import { NextPage } from "next";

import MonitorGraph from "../lib/components/layout/charts/Monitoring";
import { Page } from "../lib/components/layout/Page";

const MonitoringPage: NextPage = () => {
  return (
    <Page title="Monitoring">
      <MonitorGraph></MonitorGraph>
    </Page>
  );
};

export default MonitoringPage;
