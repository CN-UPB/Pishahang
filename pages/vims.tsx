import { NextPage } from "next";

import { VimForm } from "../lib/components/forms/vims/VimForm";
import { Page } from "../lib/components/layout/Page";

const VimPage: NextPage = () => {
  return (
    <Page title="VIM Settings">
      <VimForm />
    </Page>
  );
};

export default VimPage;
