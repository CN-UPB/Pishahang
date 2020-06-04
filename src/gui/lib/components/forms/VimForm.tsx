import { FormControl, Grid, InputLabel, MenuItem, makeStyles } from "@material-ui/core";
import { Field, Form, Formik, FormikProps, FormikValues } from "formik";
import { Select, TextField } from "formik-material-ui";
import * as React from "react";
import * as Yup from "yup";

import {
  AwsSpecificVimFields,
  KubernetesSpecificVimFields,
  OpenStackSpecificVimFields,
  VimType,
} from "../../models/Vim";

const OpenStackFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <Field component={TextField} name="openstack.address" label="Address" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="openstack.tenant.id" label="Tenant ID" />
    </Grid>
    <Grid item xs={6}>
      <Field
        component={TextField}
        name="openstack.tenant.externalNetworkId"
        label="Tenant External Network ID"
      />
    </Grid>
    <Grid item xs={6}>
      <Field
        component={TextField}
        name="openstack.tenant.externalRouterId"
        label="Tenant External Router ID"
      />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="openstack.username" label="Username" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="openstack.password" label="Password" type="password" />
    </Grid>
  </>
);

const KubernetesFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <Field component={TextField} name="kubernetes.address" label="Address" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="kubernetes.serviceToken" label="Service Token" />
    </Grid>
    <Grid item xs={12}>
      <Field component={TextField} name="kubernetes.ccc" label="Cluster CA Certificate" />
    </Grid>
  </>
);

const AwsFields: React.FunctionComponent = () => (
  <>
    <Grid item xs={6}>
      <Field component={TextField} name="aws.accessKey" label="Access Key" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="aws.secretKey" label="Secret Key" />
    </Grid>
  </>
);

const useStyles = makeStyles((theme) => ({
  select: {
    width: "100%",
  },
}));

export type VimFormValues = {
  name: string;
  country: string;
  city: string;
  openstack: OpenStackSpecificVimFields;
  kubernetes: KubernetesSpecificVimFields;
  aws: AwsSpecificVimFields;
  type: VimType | "";
};

const validationSchema = Yup.object().shape({
  name: Yup.string().required("Required"),
  country: Yup.string().required("Required"),
  city: Yup.string().required("Required"),
  type: Yup.string().required("Required"),

  aws: Yup.object().when("type", {
    is: VimType.Aws,
    then: Yup.object({
      accessKey: Yup.string().required("Required"),
      secretKey: Yup.string().required("Required"),
    }),
  }),

  kubernetes: Yup.object().when("type", {
    is: VimType.Kubernetes,
    then: Yup.object({
      address: Yup.string().required("Required"),
      serviceToken: Yup.string().required("Required"),
      ccc: Yup.string().required("Required"),
    }),
  }),

  openstack: Yup.object().when("type", {
    is: VimType.OpenStack,
    then: Yup.object({
      address: Yup.string().required("Required"),
      username: Yup.string().required("Required"),
      password: Yup.string().required("Required"),
      tenant: Yup.object().shape({
        id: Yup.string().required("Required"),
        externalNetworkId: Yup.string().required("Required"),
        externalRouterId: Yup.string().required("Required"),
      }),
    }),
  }),
});

const initialFormValues: VimFormValues = {
  country: "",
  city: "",
  name: "",
  aws: {
    accessKey: "",
    secretKey: "",
  },
  kubernetes: {
    address: "",
    serviceToken: "",
    ccc: "",
  },
  openstack: {
    address: "",
    username: "",
    password: "",
    tenant: {
      id: "",
      externalNetworkId: "",
      externalRouterId: "",
    },
  },
  type: "",
};

type Props = {
  formikRef: React.MutableRefObject<FormikValues>;
  onSubmit: (values: VimFormValues) => Promise<void>;
};

export const VimForm: React.FunctionComponent<Props> = ({ formikRef, onSubmit }) => {
  const classes = useStyles();

  return (
    <Formik
      innerRef={formikRef as any}
      initialValues={initialFormValues}
      onSubmit={onSubmit}
      validationSchema={validationSchema}
    >
      {(formikProps: FormikProps<VimFormValues>) => (
        <Form>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Field component={TextField} name="name" label="Name" />
            </Grid>
            <Grid item xs={6} container>
              <FormControl className={classes.select}>
                <InputLabel id="vim-type">Type</InputLabel>
                <Field component={Select} name="type" inputProps={{ id: "vim-type" }}>
                  <MenuItem value={VimType.OpenStack}>OpenStack</MenuItem>
                  <MenuItem value={VimType.Kubernetes}>Kubernetes</MenuItem>
                  <MenuItem value={VimType.Aws}>AWS</MenuItem>
                </Field>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <Field component={TextField} name="country" label="Country" />
            </Grid>
            <Grid item xs={6}>
              <Field component={TextField} name="city" label="City" />
            </Grid>

            {formikProps.values.type == VimType.Kubernetes && <KubernetesFields />}
            {formikProps.values.type == VimType.OpenStack && <OpenStackFields />}
            {formikProps.values.type == VimType.Aws && <AwsFields />}
          </Grid>
        </Form>
      )}
    </Formik>
  );
};
