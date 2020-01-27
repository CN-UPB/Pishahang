import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";

const VirtualMachinesPage: NextPage = () => {
  return (
    <Page title="VM Based VNF Descriptors">
      <Fab color="primary" size="small" style={{ float: "right" }} aria-label="Upload">
        <CloudUpload />
      </Fab>
      <VnfdTable></VnfdTable>
    </Page>
  );
};

export default VirtualMachinesPage;
