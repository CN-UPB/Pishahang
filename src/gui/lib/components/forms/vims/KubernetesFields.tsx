import { Grid } from "@material-ui/core";
import { Field } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";

export const KubernetesFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <Field component={TextField} name="kubernetes.vimAddressk" label="VIM Address" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="kubernetes.serviceToken" label="Service Token" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="kubernetes.cCC" label="Cluster CA Certificate" />
    </Grid>
  </>
);
