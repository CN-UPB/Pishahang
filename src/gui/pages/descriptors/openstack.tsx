import { NextPage } from "next";

import { FunctionDescriptorTable } from "../../lib/components/content/tables/FunctionDescriptorTable";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const VirtualMachinesPage: NextPage = () => {
  return (
    <Page title="OpenStack Function Descriptors">
      <FunctionDescriptorTable descriptorType={DescriptorType.OPENSTACK} />
    </Page>
  );
};

export default VirtualMachinesPage;
