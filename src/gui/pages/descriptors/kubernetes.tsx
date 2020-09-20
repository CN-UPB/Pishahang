import { NextPage } from "next";

import { DescriptorTable } from "../../lib/components/content/tables/DescriptorTable";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const ContainersPage: NextPage = () => (
  <Page title="Kubernetes Function Descriptors">
    <DescriptorTable descriptorType={DescriptorType.KUBERNETES} />
  </Page>
);

export default ContainersPage;
