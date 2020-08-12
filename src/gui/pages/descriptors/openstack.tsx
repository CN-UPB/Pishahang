import { NextPage } from "next";

import { DescriptorTable } from "../../lib/components/content/tables/DescriptorTable";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const VirtualMachinesPage: NextPage = () => (
  <Page title="OpenStack Function Descriptors">
    <DescriptorTable descriptorType={DescriptorType.OPENSTACK} />
  </Page>
);

export default VirtualMachinesPage;
