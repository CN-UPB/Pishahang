import { NextPage } from "next";

import { AddK8Form } from "../lib/components/forms/vims/AddK8Form";
import { Page } from "../lib/components/layout/Page";

const VimPage: NextPage = () => {
  return (
    <Page title="VIM Settings">
      <AddK8Form></AddK8Form>
    </Page>
  );
};

export default VimPage;
