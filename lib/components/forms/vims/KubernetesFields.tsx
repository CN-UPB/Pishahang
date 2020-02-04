import { Grid } from "@material-ui/core";
import { TextField } from "formik-material-ui";
import * as React from "react";

export const KubernetesFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <TextField name="kubernetes.vimAddressk" label="VIM Address" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="kubernetes.serviceToken" label="Service Token" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="kubernetes.cCC" label="Cluster CA Certificate" />
    </Grid>
  </>
);
