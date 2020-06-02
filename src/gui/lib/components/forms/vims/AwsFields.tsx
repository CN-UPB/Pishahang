import { Grid } from "@material-ui/core";
import { Field } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";

export const AwsFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <Field component={TextField} name="awsVim.accessKey" label="Access Key" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="awsVim.secretKey" label="Secret Key" />
    </Grid>
  </>
);
