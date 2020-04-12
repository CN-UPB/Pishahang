import axios from "axios";
import { NextPage } from "next";
import useSWR from "swr";

import { getApiUrl } from "../lib/api";
import MonitorGraph from "../lib/components/layout/charts/Monitoring";
import { Page } from "../lib/components/layout/Page";
import { PluginsTable } from "../lib/components/layout/tables/PluginsTable";

const MonitoringPage: NextPage = () => {
  const { data, error } = useSWR(getApiUrl("plugins"), axios.get);
  if (!data || error) {
    return (
      <Page title="Monitoring">
        <MonitorGraph></MonitorGraph>
      </Page>
    );
  } else {
    return (
      <Page title="Monitoring">
        <PluginsTable data={data.data}></PluginsTable>
      </Page>
    );
  }
};

export default MonitoringPage;
