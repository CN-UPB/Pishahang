import {
  Box,
  Button,
  Container,
  FormControl,
  FormHelperText,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Typography,
  makeStyles,
} from "@material-ui/core";
import { Form, Formik } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";

export const OpenStackFields: React.FunctionComponent = () => {
  const initialFormValues = {};

  return (
    <>
      <Grid container spacing={4}>
        <Grid item xs={6}>
          <TextField name="vimAddress" label="VIM Address" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="tenantId" label="Tenant ID" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="tenantExternalId" label="Tenant External Network ID" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="tenantInternalId" label="Tenant Internal Router ID" />
        </Grid>
        <Grid item xs={12}>
          <TextField name="domain" label="Domain" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="userName" label="User Name" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="password" label="Password" />
        </Grid>
      </Grid>
    </>
  );
};
