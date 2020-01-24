import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";

const ContainersPage: NextPage = () => {
  return (
    <Page title="Containers">
      <VnfdTable pageName="Container"></VnfdTable>
    </Page>
  );
};

export default ContainersPage;
