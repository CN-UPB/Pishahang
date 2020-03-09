import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/descriptorType";
import { DescriptorPageContent } from "./DescriptorPageContent";

const VirtualMachinesPage: NextPage = () => {
  return (
    <Page title="VM Based VNF Descriptors">
      <DescriptorPageContent type={DescriptorType.VM}></DescriptorPageContent>
    </Page>
  );
};

export default VirtualMachinesPage;
