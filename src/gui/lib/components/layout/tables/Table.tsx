import { Table as MuiTable, withStyles } from "@material-ui/core/";
import { Theme, createStyles } from "@material-ui/core/styles";

/**
 * A custom-styled version of the Material UI Table component.
 */
export const Table = withStyles((theme: Theme) =>
  createStyles({
    root: {
      minWidth: 650,
    },
  })
)(MuiTable);
