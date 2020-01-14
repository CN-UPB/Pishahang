import { ToolBarContent } from "../../content/toolbar/ToolBarContent";
import { AppBar, Toolbar } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import * as React from "react";

const useStyles = makeStyles(() => ({
  root: {
    flexGrow: 1,
  },
}));

export const ToolBar: React.FunctionComponent = () => {
  const classes = useStyles({});

  return (
    <div className={classes.root}>
      <AppBar position="static">
        <Toolbar>
          <ToolBarContent />
        </Toolbar>
      </AppBar>
    </div>
  );
};
