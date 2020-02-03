import { CssBaseline } from "@material-ui/core";
import { MuiThemeProvider } from "@material-ui/core/styles";
import { withReduxCookiePersist } from "next-redux-cookie-wrapper";
import withReduxSaga from "next-redux-saga";
import NextApp, { AppContext } from "next/app";
import * as React from "react";
import { ModalProvider } from "react-modal-hook";
import { Provider } from "react-redux";
import { TransitionGroup } from "react-transition-group";

import { GlobalSnackbar } from "../lib/components/layout/GlobalSnackbar";
import { makeStore } from "../lib/store";
import theme from "../lib/theme";

class App extends NextApp {
  static async getInitialProps({ Component, ctx }: AppContext) {
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
        </MuiThemeProvider>
      </Provider>
    );
  }
}

export default withReduxCookiePersist(makeStore, {
  persistConfig: {
    whitelist: ["auth"],
  },
})(withReduxSaga(App));
