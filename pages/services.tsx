import { NextPage } from "next";

import { ServicesTable } from "../lib/components/content/tables/ServicesTable";
import { Page } from "../lib/components/layout/Page";

const ServicesPage: NextPage = () => {
  return (
    <Page title="Services">
      <ServicesTable></ServicesTable>
    </Page>
  );
};

export default ServicesPage;
