import { NextPage } from "next";

import { FunctionDescriptorTable } from "../../lib/components/content/tables/FunctionDescriptorTable";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const ContainersPage: NextPage = () => {
  return (
    <Page title="AWS Function Descriptors">
      <FunctionDescriptorTable descriptorType={DescriptorType.AWS} />
    </Page>
  );
};

export default ContainersPage;
