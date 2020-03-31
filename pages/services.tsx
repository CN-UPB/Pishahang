import { NextPage } from "next";

import { Page } from "../lib/components/layout/Page";
import { ServiceInstancesTable } from "../lib/components/layout/tables/ServiceInstancesTable";
import { useDescriptorUploadDialog } from "../lib/hooks/useDescriptorUploadDialog";
import { DescriptorType } from "../lib/models/Descriptor";
import { Service } from "../lib/models/Service";

const ServicesPage: NextPage = () => {
  const showDescriptorUploadDialog = useDescriptorUploadDialog(DescriptorType.Service);

  const data: Service[] = [
    {
      id: "d8b045db-8276-45ad-bd32-bfba08da75a2",
      createdAt: "2020-03-31T13:17:39.380Z",
      updatedAt: "2020-03-31T13:17:39.380Z",
      name: "test-service",
      vendor: "my-vendor",
      version: "1.0",
    },
  ];
  return (
    <Page title="Instantiated Services">
      <ServiceInstancesTable data={data}></ServiceInstancesTable>
    </Page>
  );
};

export default ServicesPage;
