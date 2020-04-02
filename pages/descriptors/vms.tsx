import { NextPage } from "next";

import { DescriptorPageContent } from "../../lib/components/content/DescriptorPageContent";
import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/Descriptor";

const VirtualMachinesPage: NextPage = () => {
  return (
    <Page title="OpenStack Descriptors">
      <DescriptorPageContent type={DescriptorType.OPENSTACK}></DescriptorPageContent>
    </Page>
  );
};

export default VirtualMachinesPage;
