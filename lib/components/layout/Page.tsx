import {
  AppBar,
  Hidden,
  IconButton,
  Drawer as MaterialDrawer,
  Theme,
  Toolbar,
  Typography,
  createStyles,
  makeStyles,
  useTheme,
} from "@material-ui/core";
import MenuIcon from "@material-ui/icons/Menu";
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
      [theme.breakpoints.up("sm")]: {
        width: drawerWidth,
        flexShrink: 0,
      },
    },
    appBar: {
      [theme.breakpoints.up("sm")]: {
        width: `calc(100% - ${drawerWidth}px)`,
        marginLeft: drawerWidth,
      },
    },
    menuButton: {
      marginRight: theme.spacing(2),
      [theme.breakpoints.up("sm")]: {
        display: "none",
      },
    },
    toolbar: theme.mixins.toolbar,
    drawerPaper: {
      width: drawerWidth,
    },
    content: {
      flexGrow: 1,
      padding: theme.spacing(3),
    },
  })
);

type Props = {
  /**
   * The page title (will be set in the HTML <title> tag)
   */
  title?: string;
  /**
   * Whether or not to add " – Pishahang" to the title.
   */
  titleAddHomepageTitle?: boolean;
  /**
   * Whether or not to hide the drawer. Defaults to false.
   */
  hideDrawer?: boolean;
};

export const Page: React.FunctionComponent<Props> = ({
  title = "",
  titleAddHomepageTitle = true,
  hideDrawer = false,
  children,
}) => {
  const classes = useStyles({});
  const theme = useTheme();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <div className={classes.toolbar} />
      <DrawerContent />
    </div>
  );

  return (
    <div className={classes.root}>
      <Head>
        <title>{title + (titleAddHomepageTitle ? " – Pishahang" : "")}</title>
      </Head>
      <AppBar position="fixed" className={classes.appBar}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            className={classes.menuButton}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap>
            Responsive drawer
          </Typography>
        </Toolbar>
      </AppBar>
      <nav className={classes.drawer} aria-label="mailbox folders">
        <Hidden smUp implementation="css">
          <MaterialDrawer
            variant="temporary"
            anchor={"left"}
            open={mobileOpen}
            onClose={handleDrawerToggle}
            classes={{
              paper: classes.drawerPaper,
            }}
            ModalProps={{
              keepMounted: true, // Better open performance on mobile.
            }}
          >
            {drawer}
          </MaterialDrawer>
        </Hidden>
        <Hidden xsDown implementation="css">
          <MaterialDrawer
            classes={{
              paper: classes.drawerPaper,
            }}
            variant="permanent"
            open
          >
            {drawer}
          </MaterialDrawer>
        </Hidden>
      </nav>
      <main className={classes.content}>
        <div className={classes.toolbar} />
        Content
      </main>
    </div>
  );
};
