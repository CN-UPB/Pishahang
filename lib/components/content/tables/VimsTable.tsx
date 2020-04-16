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
import { DeleteForeverRounded, InfoRounded } from "@material-ui/icons";
import React from "react";

import { useVimsInfoDialog } from "../../../hooks/useVimsInfoDialog";
import { Vim } from "../../../models/Vims";
import { Table } from "../../layout/tables/Table";

type Props = {
  data: Vim[];
};

export const VimsTable: React.FunctionComponent<Props> = (props) => {
  const theme = useTheme();
  const showVimsInfoDialog = useVimsInfoDialog();

  return (
    <TableContainer component={Paper}>
      <Table aria-label="vims table">
        <TableHead>
          <TableRow>
            <TableCell>Uuid</TableCell>
            <TableCell align="center" style={{ width: "20px" }}>
              Vendor
            </TableCell>
            <TableCell align="center">Cores</TableCell>
            <TableCell align="center">Memory</TableCell>
            <TableCell align="center" style={{ width: "200px" }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {props.data.map((row) => (
            <TableRow key={row.uuid}>
              <TableCell component="th" scope="row">
                {row.uuid}
              </TableCell>
              <TableCell align="left">{row.vendor}</TableCell>
              <TableCell align="center">{row.cores}</TableCell>
              <TableCell align="center">{row.memory}</TableCell>
              <TableCell align="center">
                <Tooltip title="Info" arrow>
                  <IconButton color="primary" onClick={() => showVimsInfoDialog(row)}>
                    <InfoRounded />
                  </IconButton>
                </Tooltip>

                <Tooltip title={"Remove " + row.vimName} arrow>
                  <IconButton color="primary">
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
