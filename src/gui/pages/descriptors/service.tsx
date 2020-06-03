import { NextPage } from "next";

import { ServiceDescriptorTable } from "../../lib/components/content/tables/ServiceDescriptorTable";
import { Page } from "../../lib/components/layout/Page";

const ServicesPage: NextPage = () => (
  <Page title="Service Descriptors">
    <ServiceDescriptorTable />
  </Page>
);

export default ServicesPage;
