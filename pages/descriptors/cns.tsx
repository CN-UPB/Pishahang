import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";

const ContainersPage: NextPage = () => {
  return (
    <Page title="CN Based VNF Descriptors">
      <Fab color="secondary" size="small" style={{ float: "right" }} aria-label="Upload">
        <CloudUpload />
      </Fab>
      <VnfdTable pageName="Container"></VnfdTable>
    </Page>
  );
};

export default ContainersPage;
