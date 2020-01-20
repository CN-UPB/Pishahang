import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";

const VirtualMachinesPage: NextPage = () => {
  return (
    <Page title="Virtual Machines">
      <VnfdTable></VnfdTable>
    </Page>
  );
};

export default VirtualMachinesPage;
