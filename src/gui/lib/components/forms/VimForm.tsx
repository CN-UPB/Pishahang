import { FormControl, Grid, InputLabel, MenuItem } from "@material-ui/core";
import { Field, Form, Formik, FormikProps, FormikValues } from "formik";
import { Select, TextField } from "formik-material-ui";
import * as React from "react";
import * as yup from "yup";

import {
  AwsSpecificVimFields,
  BaseVim,
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
      <Field component={TextField} name="kubernetes.address" label="Host" />
    </Grid>
    <Grid item xs={6}>
      <Field component={TextField} name="kubernetes.port" label="Port" type="number" />
    </Grid>
    <Grid item xs={12}>
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

export type VimFormValues = Omit<BaseVim, "type"> & {
  openstack: OpenStackSpecificVimFields;
  kubernetes: KubernetesSpecificVimFields;
  aws: AwsSpecificVimFields;
  type: VimType | "";
};

const validationSchema = yup.object().shape({
  name: yup.string().required("Required"),
  country: yup.string().required("Required"),
  city: yup.string().required("Required"),
  type: yup.string().required("Required"),

  aws: yup.object().when("type", {
    is: VimType.Aws,
    then: yup.object({
      accessKey: yup.string().required("Required"),
      secretKey: yup.string().required("Required"),
    }),
  }),

  kubernetes: yup.object().when("type", {
    is: VimType.Kubernetes,
    then: yup.object({
      address: yup.string().required("Required"),
      port: yup.number().required("Required"),
      serviceToken: yup.string().required("Required"),
      ccc: yup.string().required("Required"),
    }),
  }),

  openstack: yup.object().when("type", {
    is: VimType.OpenStack,
    then: yup.object({
      address: yup.string().required("Required"),
      username: yup.string().required("Required"),
      password: yup.string().required("Required"),
      tenant: yup.object().shape({
        id: yup.string().required("Required"),
        externalNetworkId: yup.string().required("Required"),
        externalRouterId: yup.string().required("Required"),
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
    port: 443,
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
              <FormControl style={{ width: "100%" }}>
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
