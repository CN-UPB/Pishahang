import { Fab, Tooltip } from "@material-ui/core";
import { Add } from "@material-ui/icons";
import { NextPage } from "next";

import { VimForm } from "../lib/components/forms/vims/VimForm";
import { Page } from "../lib/components/layout/Page";
import { VimsTable } from "../lib/components/layout/tables/VimsTable";
import { useVimsCreaterDialog } from "../lib/hooks/useVimsCreaterDiallog";
import { Vim, VimType } from "../lib/models/Vims";

const VimPage: NextPage = () => {
  const showVimDialog = useVimsCreaterDialog();

  const data: Vim[] = [
    {
      vimName: "OpenStack",
      vimType: VimType.OpenStack,
      country: "DE",
      city: "PB",
      uuid: "adahdkad654351531515dsa51351",
      vendor: "Pishahang",
      cores: "2",
      memory: "1.2 gb",
    },
  ];
  return (
    <Page title="VIM Settings">
      <Tooltip title="Add VIM">
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
      <VimsTable data={data}></VimsTable>
    </Page>
  );
};

export default VimPage;
