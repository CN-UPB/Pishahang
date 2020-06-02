import { NextPage } from "next";
import Router from "next/router";
import React from "react";

import { LoginForm } from "./../lib/components/forms/LoginForm";
import { Page } from "../lib/components/layout/Page";
import { selectIsLoggedIn } from "../lib/store/selectors/auth";

const DashboardPage: NextPage = () => {
  return (
    <Page title="Dashboard" hideDrawer hideToolbar>
      <LoginForm />
    </Page>
  );
};

DashboardPage.getInitialProps = async ({ store, res }) => {
  // Redirect to dashboard if user is logged in
  if (selectIsLoggedIn(store.getState())) {
    if (res) {
      res.writeHead(302, {
        Location: "/",
      });
    } else {
      Router.push("/");
    }
  }
};

export default DashboardPage;
