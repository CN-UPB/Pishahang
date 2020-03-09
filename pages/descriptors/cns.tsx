import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/descriptorType";
import { DescriptorPageContent } from "./DescriptorPageContent";

const ContainersPage: NextPage = () => {
  return (
    <Page title="CN Based VNF Descriptors">
      <DescriptorPageContent type={DescriptorType.CN}></DescriptorPageContent>
    </Page>
  );
};

export default ContainersPage;
