import CircularProgress from "@material-ui/core/CircularProgress";
import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import axios from "axios";
import useSWR from "swr";

import { getApiUrl } from "../../lib/api";
import { DescriptorTable } from "../../lib/components/layout/tables/DescriptorTable";
import { useDescriptorUploadDialog } from "../../lib/hooks/useDescriptorUploadDialog";
import { DescriptorType } from "../../lib/models/DescriptorType";

type Props = {
  /**
   * Property to check page name
   */
  pageName?: any;
  type: DescriptorType;
};

export const DescriptorPageContent: React.FunctionComponent<Props> = props => {
  const showDescriptorUploadDialog = useDescriptorUploadDialog(props.type);
  const { data, error } = useSWR(getApiUrl("uploaded-descriptors?type=" + props.type), axios.get);
  //DescriptorPageContent
  if (!data || error) {
    return (
      <div>
        <Fab
          color="primary"
          size="small"
          style={{ float: "right" }}
          aria-label="Upload"
          onClick={showDescriptorUploadDialog}
        >
          <CloudUpload />
        </Fab>
        <CircularProgress
          color="secondary"
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transform: "translate(-50%, -50%)",
          }}
        />
      </div>
    );
  } else {
    return (
      <div>
        <Fab
          color="primary"
          size="small"
          style={{ float: "right" }}
          aria-label="Upload"
          onClick={showDescriptorUploadDialog}
        >
          <CloudUpload />
        </Fab>
        <DescriptorTable data={data.data}></DescriptorTable>
      </div>
    );
  }
};
