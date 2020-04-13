import { Fab, Tooltip } from "@material-ui/core";
import { Add } from "@material-ui/icons";
import axios from "axios";
import { NextPage } from "next";
import useSWR from "swr";

import { getApiUrl } from "../lib/api";
import { Page } from "../lib/components/layout/Page";
import { VimsTable } from "../lib/components/layout/tables/VimsTable";
import { useVimsCreaterDialog } from "../lib/hooks/useVimsCreaterDiallog";
import { Vim, VimType } from "../lib/models/Vims";

const VimPage: NextPage = () => {
  const showVimDialog = useVimsCreaterDialog();

  //Add fetch request
  const { data, error } = useSWR(getApiUrl("vims"), axios.get);

  const defaultData: Vim[] = [
    {
      vimName: "OpenStack",
      vimType: VimType.OpenStack,
      country: "DE",
      city: "PB",
      uuid: "f57d7590-3652-43e0-b231-6ad49e602e50",
      vendor: "Pishahang",
      cores: "2",
      memory: "1.2 gb",
    },
  ];

  if (!data || error) {
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
        <VimsTable data={defaultData}></VimsTable>
      </Page>
    );
  } else {
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
        <VimsTable data={data.data}></VimsTable>
      </Page>
    );
  }
};

export default VimPage;
