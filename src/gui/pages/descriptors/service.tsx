import { NextPage } from "next";

import { DescriptorTable } from "../../lib/components/content/tables/DescriptorTable";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const ServicesPage: NextPage = () => (
  <Page title="Service Descriptors">
    <DescriptorTable descriptorType={DescriptorType.Service} />
  </Page>
);

export default ServicesPage;
