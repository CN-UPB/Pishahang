import {
  AppBar,
  Drawer as MaterialDrawer,
  Theme,
  Toolbar,
  Typography,
  createStyles,
  makeStyles,
} from "@material-ui/core";
import Head from "next/head";
import * as React from "react";

import { DrawerContent } from "../content/drawer/DrawerContent";

const drawerWidth = 240;

const useStyles = makeStyles((theme: Theme) =>
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
    logo: {
      ...theme.mixins.toolbar,
    },
    drawerPaper: {
      width: drawerWidth,
    },
    content: {
      flexGrow: 1,
      padding: theme.spacing(3),
    },
    contentMarginTop: {
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
  /**
   * Whether or not to hide the drawer. Defaults to `false`.
   */
  hideDrawer?: boolean;
  /**
   * Whether or not to hide the toolbar. Defaults to `false`.
   */
  hideToolbar?: boolean;
};

export const Page: React.FunctionComponent<Props> = ({
  title,
  disableTitleSuffix = false,
  hideDrawer = false,
  hideToolbar = false,
  children,
}) => {
  const classes = useStyles({});

  const contentClasses = [classes.content];
  if (!hideToolbar) {
    contentClasses.push(classes.contentMarginTop);
  }

  return (
    <div className={classes.root}>
      <Head>
        <title>{title + (disableTitleSuffix ? "" : " – Pishahang")}</title>
      </Head>
      {hideDrawer || (
        <nav className={classes.drawer} aria-label="menu">
          <MaterialDrawer
            classes={{
              paper: classes.drawerPaper,
            }}
            variant="permanent"
            open
          >
            <div>
              <div className={classes.logo}>PISHAHANG</div>
              <DrawerContent />
            </div>
          </MaterialDrawer>
        </nav>
      )}
      <main className={contentClasses.join(" ")}>
        {hideToolbar || (
          <AppBar position="fixed" className={classes.appBar}>
            <Toolbar>
              <Typography variant="h6" noWrap>
                {title}
              </Typography>
            </Toolbar>
          </AppBar>
        )}
        {children}
      </main>
    </div>
  );
};
