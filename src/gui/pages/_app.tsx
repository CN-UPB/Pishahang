import { CssBaseline } from "@material-ui/core";
import { MuiThemeProvider } from "@material-ui/core/styles";
import { withReduxCookiePersist } from "next-redux-cookie-wrapper";
import NextApp, { AppContext } from "next/app";
import Router from "next/router";
import * as React from "react";
import { ModalProvider } from "react-modal-hook";
import { Provider } from "react-redux";
import { TransitionGroup } from "react-transition-group";

import { GlobalInfoDialog } from "../lib/components/layout/dialogs/GlobalInfoDialog";
import { GlobalTableDialog } from "../lib/components/layout/dialogs/GlobalTableDialog";
import { GlobalSnackbar } from "../lib/components/layout/GlobalSnackbar";
import { makeStore } from "../lib/store";
import { selectIsLoggedIn } from "../lib/store/selectors/auth";
import theme from "../lib/theme";

class App extends NextApp {
  static async getInitialProps({ Component, ctx }: AppContext) {
    const { store, res, pathname } = ctx;

    // Redirect to login page if user is not logged in
    if (pathname !== "/login" && !selectIsLoggedIn(store.getState())) {
      if (res) {
        res.writeHead(302, {
          Location: "/login",
        });
        ctx.res.end();
      } else {
        Router.push("/login");
      }
    }

    return {
      pageProps: Component.getInitialProps ? await Component.getInitialProps(ctx) : {},
    };
  }

  render() {
    const { Component, pageProps, store } = this.props as any;

    return (
      <Provider store={store}>
        <MuiThemeProvider theme={theme}>
          <CssBaseline />
          <ModalProvider container={TransitionGroup}>
            <Component {...pageProps} />
          </ModalProvider>
          <GlobalSnackbar />
          <GlobalInfoDialog />
          <GlobalTableDialog />
        </MuiThemeProvider>
      </Provider>
    );
  }
}

export default withReduxCookiePersist(makeStore, {
  persistConfig: {
    whitelist: ["auth"],
  },
})(App);
