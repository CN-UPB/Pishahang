import { Box, FormControlLabel, Grid } from "@material-ui/core";
import { Field, Form, Formik, FormikValues } from "formik";
import { Switch, TextField } from "formik-material-ui";
import { pick } from "lodash";
import * as React from "react";
import * as yup from "yup";

import { LocalUser, User } from "../../models/User";

const defaultFormValues: LocalUser = {
  username: "",
  password: "",
  fullName: "",
  email: "",
  isAdmin: false,
};

export type UserFormProps = {
  formikRef: React.MutableRefObject<FormikValues>;
  onSubmit: (values: LocalUser) => Promise<void>;
  initialValues?: LocalUser | User;
  hideIsAdminSwitch?: boolean;
};

export const UserForm: React.FunctionComponent<UserFormProps> = ({
  formikRef,
  onSubmit,
  initialValues,
  hideIsAdminSwitch,
}) => {
  const areInitialValuesSet = typeof initialValues !== "undefined";
  initialValues = {
    ...defaultFormValues,
    ...pick(initialValues, ["username", "fullName", "email", "isAdmin", "password"]),
  };

  const validationSchema: yup.ObjectSchema<LocalUser> = yup.object().shape({
    username: yup.string().required("Required").min(4, "Too short"),
    password: areInitialValuesSet
      ? yup.string()
      : yup.string().required("Required").min(8, "Too short"),
    fullName: yup.string().required("Required"),
    email: yup.string().required("Required").email("Invalid email address"),
    isAdmin: yup.boolean(),
  });

  return (
    <Formik
      innerRef={formikRef as any}
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={onSubmit}
    >
      <Form>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Field component={TextField} name="username" label="User Name" />
          </Grid>
          <Grid item xs={6}>
            <Field component={TextField} type="password" name="password" label="Password" />
          </Grid>
          <Grid item xs={6}>
            <Field component={TextField} name="fullName" label="Full Name" />
          </Grid>
          <Grid item xs={6}>
            <Field component={TextField} name="email" label="Email" />
          </Grid>
          {hideIsAdminSwitch || (
            <Grid item xs={12} container justify="center">
              <Box marginTop={2}>
                <FormControlLabel
                  control={<Field component={Switch} name="isAdmin" />}
                  label="Grant admin rights?"
                />
              </Box>
            </Grid>
          )}
        </Grid>
      </Form>
    </Formik>
  );
};
