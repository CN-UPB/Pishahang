import { NextPage } from "next";

import { DescriptorPageContent } from "../../lib/components/content/DescriptorPageContent";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const ContainersPage: NextPage = () => {
  return (
    <Page title="CN Based VNF Descriptors">
      <DescriptorPageContent type={DescriptorType.KUBERNETES}></DescriptorPageContent>
    </Page>
  );
};

export default ContainersPage;
