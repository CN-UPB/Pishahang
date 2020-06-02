import {
  IconButton,
  Paper,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from "@material-ui/core";
import { useTheme } from "@material-ui/core/styles";
import { DeleteForeverRounded, Edit, Info as InfoIcon } from "@material-ui/icons";
import * as React from "react";
import { useDispatch } from "react-redux";

import { ApiDataEndpoint } from "../../../api/endpoints";
import { InjectedAuthorizedSWRProps, withAuthorizedSWR } from "../../../hocs/withAuthorizedSWR";
import { useDescriptorDeleteDialog } from "../../../hooks/useDescriptorDeleteDialog";
import { useDescriptorEditorDialog } from "../../../hooks/useDescriptorEditorDialog";
import { showDescriptorInfoDialog } from "../../../store/actions/dialogs";
import { Table } from "../../layout/tables/Table";

type Props = InjectedAuthorizedSWRProps<
  | ApiDataEndpoint.OpenStackFunctionDescriptors
  | ApiDataEndpoint.KubernetesFunctionDescriptors
  | ApiDataEndpoint.AwsFunctionDescriptors
>;

const InternalFunctionDescriptorTable: React.FunctionComponent<Props> = ({ data }) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const showDescriptorEditorDialog = useDescriptorEditorDialog();
  const showDescriptorDeleteDialog = useDescriptorDeleteDialog();

  return (
    <TableContainer component={Paper}>
      <Table aria-label="function descriptor table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Vendor
            </TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Version
            </TableCell>
            <TableCell align="center" style={{ width: "400px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((descriptor) => (
            <TableRow key={descriptor.content.name}>
              <TableCell component="th" scope="row">
                {descriptor.content.name}
              </TableCell>
              <TableCell align="center" style={{ width: "200px" }}>
                {descriptor.content.vendor}
              </TableCell>
              <TableCell align="center" style={{ width: "200px" }}>
                {descriptor.content.version}
              </TableCell>
              <TableCell align="center" style={{ width: "400px" }}>
                <Tooltip title="Info" arrow>
                  <IconButton
                    color="primary"
                    onClick={() => dispatch(showDescriptorInfoDialog(descriptor))}
                  >
                    <InfoIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title={"Edit " + descriptor.content.name} arrow>
                  <IconButton onClick={() => showDescriptorEditorDialog(descriptor)}>
                    <Edit htmlColor={theme.palette.success.main} />
                  </IconButton>
                </Tooltip>
                <Tooltip title={"Delete " + descriptor.content.name} arrow>
                  <IconButton
                    color="primary"
                    onClick={() => showDescriptorDeleteDialog(descriptor.id)}
                  >
                    <DeleteForeverRounded htmlColor={theme.palette.error.main} />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export const OpenStackFunctionDescriptorTable = withAuthorizedSWR(
  ApiDataEndpoint.OpenStackFunctionDescriptors
)(InternalFunctionDescriptorTable);

export const KubernetesFunctionDescriptorTable = withAuthorizedSWR(
  ApiDataEndpoint.KubernetesFunctionDescriptors
)(InternalFunctionDescriptorTable);

export const AwsFunctionDescriptorTable = withAuthorizedSWR(ApiDataEndpoint.AwsFunctionDescriptors)(
  InternalFunctionDescriptorTable
);
