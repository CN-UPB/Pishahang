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
import * as Yup from "yup";

export const AwsFields: React.FunctionComponent = () => {
  const initialFormValues = {};

  return (
    <>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <TextField name="accessKey" label="Access Key" />
        </Grid>
        <Grid item xs={6}>
          <TextField name="secretKey" label="Secret Key" />
        </Grid>
      </Grid>
    </>
  );
};
