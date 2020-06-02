import { NextPage } from "next";

import { DescriptorPageContent } from "../../lib/components/content/DescriptorPageContent";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const ServicesPage: NextPage = () => {
  return (
    <Page title="Service Descriptors">
      <DescriptorPageContent type={DescriptorType.Service}></DescriptorPageContent>
    </Page>
  );
};

export default ServicesPage;
