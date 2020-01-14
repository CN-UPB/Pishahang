import { createStyles, Theme } from "@material-ui/core/styles";
import { Paper as MuiPaper, withStyles } from "@material-ui/core/";

/**
 * A custom-styled version of the Material UI Paper component.
 */
export const Paper = withStyles((theme: Theme) =>
  createStyles({
    root: {
      padding: theme.spacing(3),
    },
  })
)(MuiPaper);
