import { MainGrid } from "./MainGrid";
import { ToolBar } from "./toolbar/ToolBar";
import Head from "next/head";
import * as React from "react";

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
   * The `MainGrid`'s `Container`'s `maxWidth` property. Defaults to "lg".
   */
  maxWidth?: false | "xs" | "sm" | "md" | "lg" | "xl";
};

export const Page: React.FunctionComponent<Props> = ({
  title = "",
  titleAddHomepageTitle = true,
  maxWidth = "lg",
  children,
}) => {
  return (
    <div id="page">
      <Head>
        <title>{title + (titleAddHomepageTitle ? " – Pishahang" : "")}</title>
      </Head>
      <MainGrid maxWidth={maxWidth}>{children}</MainGrid>
    </div>
  );
};
