import { Box, Button, Container, Grid, Theme, createStyles, makeStyles } from "@material-ui/core";
import { Field, Form, Formik } from "formik";
import { TextField } from "formik-material-ui";
import { useRouter } from "next/router";
import * as React from "react";
import * as Yup from "yup";

import { registerUser } from "../../api/users";

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
  firstName: string;
  lastName: string;
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
};

export const RegistrationForm: React.FunctionComponent = () => {
  const classes = useStyles({});
  const [errorMessage, setErrorMessage] = React.useState<string>("foo");
  const router = useRouter();

  const onSubmit = async ({ confirmPassword, ...userData }: FormValues) => {
    const response = await registerUser(userData);
    console.log(response);

    //router.push("/login")
    //setErrorMessage("dsfkjsdbf")
  };

  const validationSchema = Yup.object().shape({
    firstName: Yup.string().required("Required"),
    lastName: Yup.string().required("Required"),
    email: Yup.string().email("Invalid email").required("Required"),
    username: Yup.string().required("Required"),
    password: Yup.string().required("Required"),
    confirmPassword: Yup.string()
      .required("Required")
      .oneOf([Yup.ref("password")], "Passwords do not match"),
  });

  const initialFormValues: FormValues = {
    firstName: "",
    lastName: "",
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
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
            {errorMessage}
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Field component={TextField} name="firstName" label="Name" />
              </Grid>
              <Grid item xs={12}>
                <Field component={TextField} name="lastName" label="Name" />
              </Grid>
              <Grid item xs={12}>
                <Field component={TextField} name="email" label="Email" />
              </Grid>

              <Grid item xs={12}>
                <Field component={TextField} name="username" label="User Name" />
              </Grid>
              <Grid item xs={12}>
                <Field component={TextField} name="password" label="Password" type="password" />
              </Grid>
              <Grid item xs={12}>
                <Field
                  component={TextField}
                  name="confirmPassword"
                  label="Confirm Password"
                  type="password"
                />
              </Grid>
              <Grid item xs={12} container alignItems="center" justify="center">
                <Box paddingTop={3}>
                  <Button type="submit" variant="contained" color="primary">
                    Register
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Form>
      </Formik>
    </Container>
  );
};
