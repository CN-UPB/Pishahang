import { NextPage } from "next";

import { VimsTable } from "../lib/components/content/tables/VimsTable";
import { Page } from "../lib/components/layout/Page";

const VimPage: NextPage = () => {
  return (
    <Page title="Virtual Infrastructure Managers">
      <VimsTable></VimsTable>
    </Page>
  );
};

export default VimPage;
