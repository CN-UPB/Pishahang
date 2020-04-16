import axios from "axios";
import { NextPage } from "next";
import useSWR from "swr";

import { getApiUrl } from "../lib/api";
import { PluginsTable } from "../lib/components/content/tables/PluginsTable";
import MonitorGraph from "../lib/components/layout/charts/Monitoring";
import { Page } from "../lib/components/layout/Page";

const MonitoringPage: NextPage = () => {
  return (
    <Page title="Monitoring">
      <PluginsTable></PluginsTable>
    </Page>
  );
};

export default MonitoringPage;
