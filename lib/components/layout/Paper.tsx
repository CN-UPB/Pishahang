import { Paper as MuiPaper, withStyles } from "@material-ui/core/";
import { Theme, createStyles } from "@material-ui/core/styles";

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
