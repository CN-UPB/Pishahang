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

export const KubernetesFields: React.FunctionComponent = () => {
  const initialFormValues = {};

  return (
    <>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <TextField name="vimAddress" label="VIM Address" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="serviceToken" label="Service Token" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="cCC" label="Cluster CA Certificate" />
        </Grid>
      </Grid>
    </>
  );
};
