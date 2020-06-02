import { Fab, Tooltip } from "@material-ui/core";
import { Add } from "@material-ui/icons";
import axios from "axios";
import { NextPage } from "next";
import useSWR from "swr";

import { getApiUrl } from "../lib/api";
import { VimsTable } from "../lib/components/content/tables/VimsTable";
import { Page } from "../lib/components/layout/Page";
import { useVimsCreaterDialog } from "../lib/hooks/useVimsCreaterDiallog";
import { Vim, VimType } from "../lib/models/Vims";

const VimPage: NextPage = () => {
  const showVimDialog = useVimsCreaterDialog();
  return (
    <Page title="VIM Settings">
      <Tooltip title="Add VIM" arrow>
        <Fab
          color="primary"
          size="small"
          style={{ float: "right" }}
          aria-label="Upload"
          onClick={showVimDialog}
        >
          <Add />
        </Fab>
      </Tooltip>
      <VimsTable></VimsTable>
    </Page>
  );
};

export default VimPage;
