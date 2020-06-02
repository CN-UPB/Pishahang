import {
  Box,
  Button,
  Container,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Typography,
  makeStyles,
} from "@material-ui/core";
import { Field, Form, Formik, FormikProps } from "formik";
import { Select, TextField } from "formik-material-ui";
import * as React from "react";
import * as Yup from "yup";

type FormValues = {
  name: string;
  email: string;
  country: string;
  companyName: string;
  username: string;
  password: string;
};

export const UserProfile: React.FunctionComponent = () => {
  const onSubmit = async () => {};

  const initialFormValues: FormValues = {
    name: "",
    email: "",
    country: "",
    companyName: "",
    username: "",
    password: "",
  };

  return (
    <Container maxWidth={"md"}>
      <Formik initialValues={initialFormValues} onSubmit={onSubmit}>
        <Form>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Field component={TextField} name="name" label="Name" />
            </Grid>
            <Grid item xs={6}>
              <Field component={TextField} name="email" label="Email" />
            </Grid>
            <Grid item xs={6}>
              <Field component={TextField} name="companyName" label="Company Name" />
            </Grid>
            <Grid item xs={6}>
              <Field component={TextField} name="country" label="Country" />
            </Grid>
            <Grid item xs={6}>
              <Field component={TextField} name="username" label="User Name" />
            </Grid>
            <Grid item xs={6}>
              <Field component={TextField} name="password" label="Password" />
            </Grid>
            <Grid item xs={12} container alignItems="center" justify="center">
              <Box paddingTop={3}>
                <Button type="submit" variant="contained" color="primary">
                  Submit
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Form>
      </Formik>
    </Container>
  );
};
