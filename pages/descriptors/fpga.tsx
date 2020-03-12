import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { DescriptorType } from "../../lib/models/descriptorType";
import { DescriptorPageContent } from "./DescriptorPageContent";

const ContainersPage: NextPage = () => {
  return (
    <Page title="FPGA Based VNF Descriptors">
      <DescriptorPageContent type={DescriptorType.FPGA}></DescriptorPageContent>
    </Page>
  );
};

export default ContainersPage;
