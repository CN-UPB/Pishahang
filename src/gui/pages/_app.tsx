import { CssBaseline } from "@material-ui/core";
import { MuiThemeProvider } from "@material-ui/core/styles";
import { withReduxCookiePersist } from "next-redux-cookie-wrapper";
import { ReduxWrapperAppProps } from "next-redux-wrapper";
import NextApp, { AppContext } from "next/app";
import Head from "next/head";
import Router from "next/router";
import * as React from "react";
import { ModalProvider } from "react-modal-hook";
import { Provider } from "react-redux";
import { TransitionGroup } from "react-transition-group";
import { RootState } from "StoreTypes";

import { DescriptorEditorDialog } from "../lib/components/layout/dialogs/DescriptorEditorDialog";
import { GlobalInfoDialog } from "../lib/components/layout/dialogs/GlobalInfoDialog";
import { GlobalTableDialog } from "../lib/components/layout/dialogs/GlobalTableDialog";
import { GlobalSnackbar } from "../lib/components/layout/GlobalSnackbar";
import { makeStore } from "../lib/store";
import { selectIsLoggedIn } from "../lib/store/selectors/auth";
import theme from "../lib/theme";

class App extends NextApp<ReduxWrapperAppProps<RootState>> {
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
    const { Component, pageProps, store } = this.props;

    return (
      <>
        <Head>
          <meta
            name="viewport"
            content="minimum-scale=1, initial-scale=1, width=device-width, shrink-to-fit=no"
          />
        </Head>
        <Provider store={store}>
          <MuiThemeProvider theme={theme}>
            <CssBaseline />
            <ModalProvider container={TransitionGroup}>
              <Component {...pageProps} />
              <DescriptorEditorDialog />
            </ModalProvider>
            <GlobalSnackbar />
            <GlobalInfoDialog />
            <GlobalTableDialog />
          </MuiThemeProvider>
        </Provider>
      </>
    );
  }
}

export default withReduxCookiePersist(makeStore, {
  persistConfig: { whitelist: ["auth"] },
})(App);
