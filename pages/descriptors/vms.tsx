import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import axios from "axios";
import { NextPage } from "next";
import useSWR, { ConfigInterface } from "swr";

import { getApiUrl } from "../../lib/api";
import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";
import { useDescriptorUploadDialog } from "../../lib/hooks/useDescriptorUploadDialog";
import { DescriptorType } from "../../lib/models/descriptorType";
import { VnfdMeta } from "../../lib/models/VnfdMeta";

const VirtualMachinesPage: NextPage = () => {
  const showDescriptorUploadDialog = useDescriptorUploadDialog(DescriptorType.VM);
  const { data, error } = useSWR(getApiUrl("uploaded-descriptors?type=vm"), axios.get);

  if (error || !data) {
    return <div>Loading...</div>;
  }

  return (
    <Page title="VM Based VNF Descriptors">
      <Fab
        color="primary"
        size="small"
        style={{ float: "right" }}
        aria-label="Upload"
        onClick={showDescriptorUploadDialog}
      >
        <CloudUpload />
      </Fab>
      <VnfdTable data={data.data}></VnfdTable>
    </Page>
  );
};

export default VirtualMachinesPage;
