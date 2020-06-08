import {
  AppBar,
  Drawer as MaterialDrawer,
  Toolbar,
  Typography,
  createStyles,
  makeStyles,
} from "@material-ui/core";
import Head from "next/head";
import * as React from "react";

import { DrawerContent } from "../content/DrawerContent";
import { RightToolbarContent } from "../content/RightToolbarContent";

const drawerWidth = 280;

const useStyles = makeStyles((theme) =>
  createStyles({
    root: {
      display: "flex",
    },
    drawer: {
      width: drawerWidth,
      flexShrink: 0,
    },
    appBar: {
      width: `calc(100% - ${drawerWidth}px)`,
      marginLeft: drawerWidth,
    },
    toolbar: {
      justifyContent: "space-between",
    },
    rightToolbarContent: {
      display: "flex",
      flexWrap: "nowrap",
    },
    logoContainer: {
      ...theme.mixins.toolbar,
      height: `calc(${theme.mixins.toolbar.minHeight} * 2px)`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    },
    logo: {
      maxHeight: "80%",
    },
    drawerPaper: {
      width: drawerWidth,
    },
    content: {
      flexGrow: 1,
      padding: theme.spacing(3),
      paddingTop: theme.spacing(4),
      marginTop: theme.mixins.toolbar.minHeight,
    },
  })
);

type Props = {
  /**
   * The page title (will be set as the document title and in the toolbar)
   */
  title: string;
  /**
   * Whether to hide " – Pishahang" in the document title. Defaults to `false`.
   */
  disableTitleSuffix?: boolean;
};

export const Page: React.FunctionComponent<Props> = ({
  title,
  disableTitleSuffix = false,
  children,
}) => {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <Head>
        <title>{title + (disableTitleSuffix ? "" : " – Pishahang")}</title>
      </Head>
      <nav className={classes.drawer} aria-label="menu">
        <MaterialDrawer
          classes={{
            paper: classes.drawerPaper,
          }}
          variant="permanent"
          open
        >
          <div>
            <div className={classes.logoContainer}>
              <img className={classes.logo} src="/img/logo.svg" />
            </div>
            <DrawerContent />
          </div>
        </MaterialDrawer>
      </nav>
      <main className={classes.content}>
        <AppBar position="fixed" className={classes.appBar}>
          <Toolbar className={classes.toolbar}>
            <Typography variant="h6" noWrap>
              {title}
            </Typography>
            <RightToolbarContent className={classes.rightToolbarContent} />
          </Toolbar>
        </AppBar>
        {children}
      </main>
    </div>
  );
};
