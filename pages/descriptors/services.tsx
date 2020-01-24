import { NextPage } from "next";

import { Page } from "../lib/components/layout/Page";
import { ServicesTable } from "../lib/components/layout/tables/ServicesTable";

const ServicesPage: NextPage = () => {
  return (
    <Page title="Services">
      <ServicesTable></ServicesTable>
    </Page>
  );
};

export default ServicesPage;
