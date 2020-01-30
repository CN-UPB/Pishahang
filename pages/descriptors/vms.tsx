import Fab from "@material-ui/core/Fab";
import { CloudUpload } from "@material-ui/icons";
import { NextPage } from "next";

import { Page } from "../../lib/components/layout/Page";
import { VnfdTable } from "../../lib/components/layout/tables/VnfdTable";
import { VnfdMeta } from "../../lib/models/VnfdMeta";

const VirtualMachinesPage: NextPage = () => {
  const data: VnfdMeta[] = [
    {
      status: "active",
      signature: "null",
      md5: "a051247412cc8f0d68ad62f6c0b68fbb",
      updated_at: new Date(),
      created_at: new Date(),
      username: "null",
      descriptor: {
        name: "forwarder-vm-vnf",
        vendor: "eu.sonata-nfv.vnf-descriptor",
        version: "1.0",
        author: "Elton John",
        description: "ICMP ping request forwarder; VM-based VNF",
        descriptor_version: "vnfd-schema-01",
        virtual_deployment_units: "",
      },
      uuid: "d885fbd7-e474-41a1-8c11-628024984210",
    },
  ];

  return (
    <Page title="VM Based VNF Descriptors">
      <Fab color="primary" size="small" style={{ float: "right" }} aria-label="Upload">
        <CloudUpload />
      </Fab>
      <VnfdTable data={data}></VnfdTable>
    </Page>
  );
};

export default VirtualMachinesPage;
