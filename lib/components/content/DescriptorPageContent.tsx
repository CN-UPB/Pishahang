import CircularProgress from "@material-ui/core/CircularProgress";
import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import axios from "axios";
import useSWR from "swr";

import { getApiUrl } from "../../api";
import { useDescriptorUploadDialog } from "../../hooks/useDescriptorUploadDialog";
import { DescriptorType } from "../../models/Descriptor";
import { FunctionDescriptorTable } from "../layout/tables/FunctionDescriptorTable";
import { ServiceDescriptorTable } from "../layout/tables/ServiceDescriptorTable";

type Props = {
  type: DescriptorType;
};

export const DescriptorPageContent: React.FunctionComponent<Props> = ({ type }) => {
  const showDescriptorUploadDialog = useDescriptorUploadDialog(type);
  const { data, error } = useSWR(getApiUrl("descriptors?type=" + type), axios.get);
  //DescriptorPageContent
  // console.log(type);

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
        {type == DescriptorType.Service && (
          <ServiceDescriptorTable data={data.data}></ServiceDescriptorTable>
        )}
        {type != DescriptorType.Service && (
          <FunctionDescriptorTable data={data.data}></FunctionDescriptorTable>
        )}
      </div>
    );
  }
};
