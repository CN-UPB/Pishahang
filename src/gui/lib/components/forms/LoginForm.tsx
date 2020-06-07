import { Box, Button, Container, Grid, Typography } from "@material-ui/core";
import { Field, Form, Formik } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";
import { useSelector } from "react-redux";
import * as Yup from "yup";

import { useThunkDispatch } from "../../store";
import { selectLoginErrorMessage } from "../../store/selectors/auth";
import { login } from "../../store/thunks/auth";

type FormValues = {
  username: string;
  password: string;
};

export const LoginForm: React.FunctionComponent = () => {
  const loginErrorMessage = useSelector(selectLoginErrorMessage);
  const dispatch = useThunkDispatch();

  const onSubmit = async (values: FormValues) => dispatch(login(values.username, values.password));

  const validationSchema = Yup.object().shape({
    username: Yup.string().required("Required"),
    password: Yup.string().required("Required"),
  });

  const initialFormValues: FormValues = {
    username: "",
    password: "",
  };

  return (
    <Container style={{ maxWidth: "400px" }}>
      <Formik
        initialValues={initialFormValues}
        onSubmit={onSubmit}
        validationSchema={validationSchema}
      >
        <Form>
          <Grid container spacing={2}>
            <Grid item xs={12} container alignItems="center" justify="center">
              <img src="/img/logo.svg" />
            </Grid>
            {loginErrorMessage && (
              <Grid item xs={12}>
                <Typography color="error" align="center">
                  {loginErrorMessage}
                </Typography>
              </Grid>
            )}
            <Grid item xs={12}>
              <Field component={TextField} name="username" label="User Name" />
            </Grid>
            <Grid item xs={12}>
              <Field component={TextField} name="password" label="Password" type="password" />
            </Grid>
            <Grid item xs={12} container alignItems="center" justify="center">
              <Box paddingTop={3}>
                <Button type="submit" variant="contained" color="primary">
                  Login
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Form>
      </Formik>
    </Container>
  );
};
