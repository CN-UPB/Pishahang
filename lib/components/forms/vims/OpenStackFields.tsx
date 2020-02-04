import { Grid } from "@material-ui/core";
import { TextField } from "formik-material-ui";
import * as React from "react";

export const OpenStackFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <TextField name="openStack.vimAddress" label="VIM Address" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="openStack.tenantId" label="Tenant ID" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="openStack.tenantExternalId" label="Tenant External Network ID" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="openStack.tenantInternalId" label="Tenant Internal Router ID" />
    </Grid>
    <Grid item xs={12}>
      <TextField name="openStack.domain" label="Domain" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="openStack.userName" label="User Name" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="openStack.password" label="Password" />
    </Grid>
  </>
);
