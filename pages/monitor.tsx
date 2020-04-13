import axios from "axios";
import { NextPage } from "next";
import useSWR from "swr";

import { getApiUrl } from "../lib/api";
import MonitorGraph from "../lib/components/layout/charts/Monitoring";
import { Page } from "../lib/components/layout/Page";
import { PluginsTable } from "../lib/components/layout/tables/PluginsTable";

const MonitoringPage: NextPage = () => {
  return (
    <Page title="Monitoring">
      <PluginsTable></PluginsTable>
    </Page>
  );
};

export default MonitoringPage;
