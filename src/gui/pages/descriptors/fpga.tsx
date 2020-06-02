import { NextPage } from "next";

import { DescriptorPageContent } from "../../lib/components/content/DescriptorPageContent";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const ContainersPage: NextPage = () => {
  return (
    <Page title="AWS Descriptors">
      <DescriptorPageContent type={DescriptorType.AWS}></DescriptorPageContent>
    </Page>
  );
};

export default ContainersPage;
