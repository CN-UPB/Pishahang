import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Typography,
} from "@material-ui/core";
import * as React from "react";

type Props = {
  /**
   * The table's content as a list of [title, value] pairs
   */
  content: [string, string][];
};

/**
 * A table for displaying [title, value] string pairs
 */
export const InfoDialogTable: React.FunctionComponent<Props> = ({ content }) => (
  <TableContainer component={Paper}>
    <Table aria-label="simple table">
      <TableBody>
        {content.map(entry => (
          <TableRow key={entry[0]}>
            <TableCell component="th" scope="row">
              <Typography variant="body2" gutterBottom>
                {entry[0]}:
              </Typography>
            </TableCell>
            <TableCell align="left">{entry[1]}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);
