import { Box, Button, Container, Grid, Typography } from "@material-ui/core";
import { Form, Formik } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";

type FormValues = {
  test1: string;
  test2: string;
  test3: string;
};

export const AddK8Form: React.FunctionComponent = () => {
  const initialFormValues = {};

  const onSubmit = async (values: FormValues) => {
    alert(values.test2);
  };

  return (
    <Container maxWidth={"md"}>
      <Formik initialValues={initialFormValues} onSubmit={onSubmit}>
        <Form>
          <Typography variant="h4" align="center">
            Caption
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <TextField name="test1" label="Test1" />
            </Grid>
            <Grid item xs={6}>
              <TextField name="test2" label="Test2" />
            </Grid>
            <Grid item xs={4}>
              <TextField name="test3" label="Test3" />
            </Grid>
            <Grid item xs={12} container alignItems="center" justify="center">
              <Button type="submit" variant="contained" color="primary">
                Submit
              </Button>
            </Grid>
          </Grid>
        </Form>
      </Formik>
    </Container>
  );
};
