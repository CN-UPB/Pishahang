import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/DescriptorType";
import { DescriptorPageContent } from "./DescriptorPageContent";

const ServicesPage: NextPage = () => {
  return (
    <Page title="Services Descriptors">
      <DescriptorPageContent type={DescriptorType.Service}></DescriptorPageContent>
    </Page>
  );
};

export default ServicesPage;
