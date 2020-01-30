import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { ServicesTable } from "../../lib/components/layout/tables/ServicesTable";

const ServicesPage: NextPage = () => {
  return (
    <Page title="Services Descriptors">
      <Fab color="secondary" size="small" style={{ float: "right" }} aria-label="Upload">
        <CloudUpload />
      </Fab>
      <ServicesTable></ServicesTable>
    </Page>
  );
};

export default ServicesPage;
