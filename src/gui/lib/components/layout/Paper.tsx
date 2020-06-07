import { Paper as MuiPaper, withStyles } from "@material-ui/core/";
import { createStyles } from "@material-ui/core/styles";

/**
 * A custom-styled version of the Material UI Paper component.
 */
export const Paper = withStyles((theme) =>
  createStyles({
    root: {
      padding: theme.spacing(3),
    },
  })
)(MuiPaper);
