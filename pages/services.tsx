import { NextPage } from "next";

import { Page } from "../lib/components/layout/Page";
import { ServiceInstancesTable } from "../lib/components/layout/tables/ServiceInstancesTable";
import { useDescriptorUploadDialog } from "../lib/hooks/useDescriptorUploadDialog";
import { Service } from "../lib/models/Service";

const ServicesPage: NextPage = () => {
  const showDescriptorUploadDialog = useDescriptorUploadDialog();

  const data: Service[] = [
    {
      status: "active",
      signature: "null",
      md5: "832116ac25c690cab0b7caa3f5cc2fc4",
      updated_at: new Date(),
      created_at: new Date(),
      username: "null",
      uuid: "d8b045db-8276-45ad-bd32-bfba08da75a2",
      cosd: {
        descriptor_version: "1.0",
        vendor: "eu.sonata-nfv.service-descriptor",
        name: "ICMP-forwarder",
        version: "1.0",
        author: "Elton John",
        description: "ICMP forwarder; consists of CN- and VM-based VNFs",
        network_functions: "null",
        cloud_services: "null",
        forwarding_graphs: "null",
      },
    },
  ];
  return (
    <Page title="Instantiated Services">
      <ServiceInstancesTable data={data}></ServiceInstancesTable>
    </Page>
  );
};

export default ServicesPage;
