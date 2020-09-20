import { Grid, Typography } from "@material-ui/core";
import { Field, Form, Formik, FormikValues } from "formik";
import { TextField } from "formik-material-ui";
import * as React from "react";
import * as yup from "yup";

export type InstantiationFormValues = {
  ingresses: string;
  egresses: string;
};

const initialValues: InstantiationFormValues = {
  ingresses: "",
  egresses: "",
};

export type InstantiationFormProps = {
  formikRef: React.MutableRefObject<FormikValues>;
  onSubmit: (values: InstantiationFormValues) => Promise<void>;
};

export const InstantiationForm: React.FunctionComponent<InstantiationFormProps> = ({
  formikRef,
  onSubmit,
}) => {
  const validationSchema: yup.ObjectSchema<InstantiationFormValues> = yup.object().shape({
    ingresses: yup.string(),
    egresses: yup.string(),
  });

  return (
    <Formik
      innerRef={formikRef as any}
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={onSubmit}
    >
      <Form>
        <Typography>
          You may optionally enter comma-separated lists of ingresses and egresses (domain names or
          IP addresses) for the new service instance:
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Field component={TextField} name="ingresses" label="Ingresses" />
          </Grid>
          <Grid item xs={6}>
            <Field component={TextField} name="egresses" label="Egresses" />
          </Grid>
        </Grid>
      </Form>
    </Formik>
  );
};
