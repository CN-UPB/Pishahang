import { Box, Button, Container, Grid, Theme, createStyles, makeStyles } from "@material-ui/core";
import { Field, Form, Formik } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";
import { useDispatch, useSelector } from "react-redux";
import * as Yup from "yup";

import { login } from "./../../store/actions/auth";
import { selectLoginErrorMessage } from "../../store/selectors/auth";

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
  username: string;
  password: string;
};

export const LoginForm: React.FunctionComponent = () => {
  const classes = useStyles({});
  const loginErrorMessage = useSelector(selectLoginErrorMessage);
  const dispatch = useDispatch();

  const onSubmit = async (values: FormValues) => dispatch(login(values));

  const validationSchema = Yup.object().shape({
    username: Yup.string().required("Required"),
    password: Yup.string().required("Required"),
  });

  const initialFormValues: FormValues = {
    username: "",
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
              {loginErrorMessage}
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
          </Box>
        </Form>
      </Formik>
    </Container>
  );
};
