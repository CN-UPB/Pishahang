import { NextPage } from "next";

import { ApiDataEndpoint } from "../lib/api/endpoints";
import { ServicesTable } from "../lib/components/content/tables/ServicesTable";
import { Page } from "../lib/components/layout/Page";
import { useAuthorizedSWR } from "../lib/hooks/useAuthorizedSWR";
import { useDescriptorUploadDialog } from "../lib/hooks/useDescriptorUploadDialog";
import { DescriptorType } from "../lib/models/Descriptor";

const ServicesPage: NextPage = () => {
  const showDescriptorUploadDialog = useDescriptorUploadDialog(DescriptorType.Service);
  const { data, error } = useAuthorizedSWR(ApiDataEndpoint.Services);

  if (!data || error) {
    return <Page title="Services">Error...</Page>;
  } else {
    return (
      <Page title="Services">
        <ServicesTable data={data}></ServicesTable>
      </Page>
    );
  }
};

export default ServicesPage;
