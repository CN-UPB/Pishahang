import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";

const ContainersPage: NextPage = () => {
  return (
    <Page title="CN Based VNF Descriptors">
      <VnfdTable pageName="Container"></VnfdTable>
    </Page>
  );
};

export default ContainersPage;
