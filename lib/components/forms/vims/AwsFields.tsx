import { Grid } from "@material-ui/core";
import { TextField } from "formik-material-ui";
import * as React from "react";

export const AwsFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <TextField name="accessKey" label="Access Key" />
    </Grid>
    <Grid item xs={6}>
      <TextField name="secretKey" label="Secret Key" />
    </Grid>
  </>
);
