import { Grid } from "@material-ui/core";
import { TextField } from "formik-material-ui";
import * as React from "react";

export const KubernetesFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <TextField name="vimAddress" label="VIM Address" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="serviceToken" label="Service Token" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="cCC" label="Cluster CA Certificate" />
    </Grid>
  </>
);
