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
  Typography,
  makeStyles,
} from "@material-ui/core";
import { Form, Formik, FormikProps } from "formik";
import { Select, TextField } from "formik-material-ui";
import * as React from "react";
import * as Yup from "yup";

import { AwsFields } from "./AwsFields";
import { KubernetesFields } from "./KubernetesFields";
import { OpenStackFields } from "./OpenStackFields";

enum VimType {
  OpenStack,
  Kubernetes,
  Aws,
}

// Style design for VIM-Vendor drop down menu using formcontrol and makeStyles
const useStyles = makeStyles(theme => ({
  formControl: {
    margin: theme.spacing(1),
    width: "100%",
  },
  selectEmpty: {
    marginTop: theme.spacing(2),
  },
}));

type FormValues = {
  vimName: string;
  country: string;
  city: string;
  kubernetes: {
    vIMAddess: string;
    serviceToken: string;
    cCC: string;
  };
  awsVim: {
    accessKey: string;
    secretKey: string;
  };
  openStack: {
    vIMAddess: string;
    tenantId: string;
    tenantExternalId: string;
    tenantInternalId: string;
    userName: string;
    password: string;
  };

  vimType: VimType;
};

export const VimForm: React.FunctionComponent = () => {
  const initialFormValues = {};
  const classes = useStyles(1);
  const onSubmit = async (values: FormValues) => {
    alert(values.city);
  };
  const validationSchema = Yup.object().shape({
    country: Yup.string().required("Required"),
    city: Yup.string().required("Required"),
    vimName: Yup.string().required("Required"),
    vimVendor: Yup.string().required("Required"),
    accessKey: Yup.string().required("Required"),
    secretKey: Yup.string().required("Required"),
    vimAddress: Yup.string().required("Required"),
    tenantId: Yup.string().required("Required"),
    tenantExternalId: Yup.string().required("Required"),
    tenantInternalId: Yup.string().required("Required"),
    domain: Yup.string().required("Required"),
    userName: Yup.string().required("Required"),
    password: Yup.string().required("Required"),
    serviceToken: Yup.string().required("Required"),
    cCC: Yup.string().required("Required"),
  });

  return (
    <Container maxWidth={"md"}>
      <Formik
        initialValues={initialFormValues}
        onSubmit={onSubmit}
        validationSchema={validationSchema}
      >
        {(formikProps: FormikProps<FormValues>) => (
          <Form>
            <Typography variant="h4" align="center">
              Set Virtual Infrastructure Manager
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField name="country" label="Country" />
              </Grid>
              <Grid item xs={6}>
                <TextField name="city" label="City" />
              </Grid>
              <Grid item xs={6}>
                <TextField name="vimName" label="VIM Name" />
              </Grid>
              <Grid item xs={6} container justify="center">
                <FormControl className={classes.formControl}>
                  <InputLabel id="vimVendor">VIM Vendor</InputLabel>
                  <Select name="vimType">
                    <MenuItem value={VimType.Kubernetes}>Kubernetes</MenuItem>
                    <MenuItem value={VimType.OpenStack}>Openstack</MenuItem>
                    <MenuItem value={VimType.Aws}>AWS VIM</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              {formikProps.values.vimType == VimType.Kubernetes && <KubernetesFields />}
              {formikProps.values.vimType == VimType.OpenStack && <OpenStackFields />}
              {formikProps.values.vimType == VimType.Aws && <AwsFields />}
              <Grid item xs={12} container alignItems="center" justify="center">
                <Box paddingTop={3}>
                  <Button variant="contained" color="primary">
                    Submit
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Form>
        )}
      </Formik>
    </Container>
  );
};
