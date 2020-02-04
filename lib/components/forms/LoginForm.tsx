import { Box, Button, Container, Grid, Theme, createStyles, makeStyles } from "@material-ui/core";
import { Form, Formik } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";
import * as Yup from "yup";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    logoContainer: {
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      paddingBottom: theme.spacing(2),
    },
    logo: {
      width: "100%",
    },
  })
);

type FormValues = {
  email: string;
  password: string;
};

export const LoginForm: React.FunctionComponent = () => {
  const classes = useStyles({});

  const onSubmit = () => {};

  const validationSchema = Yup.object().shape({
    email: Yup.string()
      .email("Invalid email")
      .required("Required"),
    password: Yup.string().required("Required"),
    confirmPassword: Yup.string()
      .required("Required")
      .oneOf([Yup.ref("password")], "Password does not match"),
  });

  const initialFormValues: FormValues = {
    email: "",
    password: "",
  };

  return (
    <Container maxWidth={"xs"}>
      <Formik
        initialValues={initialFormValues}
        onSubmit={onSubmit}
        validationSchema={validationSchema}
      >
        <Form>
          <Box padding={6}>
            <div className={classes.logoContainer}>
              <img className={classes.logo} src="/img/logo.svg" />
            </div>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField name="email" label="Email" />
              </Grid>
              <Grid item xs={12}>
                <TextField name="password" label="Password" />
              </Grid>
              <Grid item xs={12} container alignItems="center" justify="center">
                <Box paddingTop={3}>
                  <Button variant="contained" color="primary">
                    Login
                  </Button>
                </Box>
              </Grid>
              <Grid container alignItems="center" justify="center">
                <a href="">or, Register</a>
              </Grid>
            </Grid>
          </Box>
        </Form>
      </Formik>
    </Container>
  );
};
