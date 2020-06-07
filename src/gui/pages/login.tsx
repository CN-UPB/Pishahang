import { createStyles, makeStyles } from "@material-ui/core";
import { NextPage } from "next";
import Head from "next/head";
import Router from "next/router";
import React from "react";

import { LoginForm } from "./../lib/components/forms/LoginForm";
import { selectIsLoggedIn } from "../lib/store/selectors/auth";

const useStyles = makeStyles((theme) =>
  createStyles({
    root: {
      display: "flex",
      justifyContent: "center",
      paddingTop: theme.spacing(6),
    },
    content: {
      padding: theme.spacing(3),
    },
  })
);

const LoginPage: NextPage = () => {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <Head>
        <title>Pishahang Login</title>
      </Head>
      <main className={classes.content}>
        <LoginForm />
      </main>
    </div>
  );
};

LoginPage.getInitialProps = async ({ store, res }) => {
  // Redirect to dashboard if user is already logged in
  if (selectIsLoggedIn(store.getState())) {
    if (res) {
      res.writeHead(302, {
        Location: "/",
      });
      res.end();
    } else {
      Router.push("/");
    }
  }
};

export default LoginPage;
