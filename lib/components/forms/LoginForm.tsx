import {
  Box,
  Button,
  Container,
  FormControl,
  FormHelperText,
  Grid,
  InputLabel,
  Link,
  MenuItem,
  Theme,
  Typography,
  createStyles,
  makeStyles,
} from "@material-ui/core";
import { ErrorMessage, Form, Formik, FormikProps } from "formik";
import { Select, TextField } from "formik-material-ui";
import * as React from "react";
import * as Yup from "yup";

type FormValues = {
  email: string;
  password: string;
};
const drawerWidth = 240;
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

export const LoginForm: React.FunctionComponent = () => {
  const initialFormValues = {};
  const classes = useStyles({});
  const onSubmit = async (values: FormValues) => {};

  const validationSchema = Yup.object().shape({
    email: Yup.string()
      .email("Invalid email")
      .required("Required"),
    password: Yup.string().required("Required"),
    confirmPassword: Yup.string()
      .required("Required")
      .oneOf([Yup.ref("password")], "Password does not match"),
  });

  return (
    <Container maxWidth={"xs"}>
      <Formik
        initialValues={initialFormValues}
        onSubmit={onSubmit}
        validationSchema={validationSchema}
      >
        {(formikProps: FormikProps<FormValues>) => (
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
        )}
      </Formik>
    </Container>
  );
};
