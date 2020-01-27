import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";

const VirtualMachinesPage: NextPage = () => {
  return (
    <Page title="VM Based VNF Descriptors">
      <Fab variant="extended" color="primary" size="small" style={{ float: "right" }}>
        <CloudUpload />
      </Fab>
      <VnfdTable></VnfdTable>
    </Page>
  );
};

export default VirtualMachinesPage;
