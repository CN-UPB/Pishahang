import Fab from "@material-ui/core/Fab";
import { CloudUpload, DateRange } from "@material-ui/icons";
import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";
import { VnfdMeta } from "../../lib/models/VnfdMeta";

const ContainersPage: NextPage = () => {
  const data: VnfdMeta[] = [
    {
      status: "active",
      signature: "null",
      md5: "43c1b014db0ce887288ea95391b0cd10",
      updated_at: new Date(),
      created_at: new Date(),
      username: "null",
      descriptor: {
        name: "forwarder-vm-vnf",
        vendor: "eu.sonata-nfv.cloud-service-descriptor",
        version: "1.0",
        author: "Elton John",
        description: "ICMP ping request forwarder; container-based VNF.",
        descriptor_version: "2.0",
        virtual_deployment_units: "",
      },
      uuid: "66695e0f-5472-4f85-a310-fe0676bf28e6",
    },
  ];

  return (
    <Page title="CN Based VNF Descriptors">
      <Fab color="primary" size="small" style={{ float: "right" }} aria-label="Upload">
        <CloudUpload />
      </Fab>
      <VnfdTable pageName="Container" data={data}></VnfdTable>
    </Page>
  );
};

export default ContainersPage;
