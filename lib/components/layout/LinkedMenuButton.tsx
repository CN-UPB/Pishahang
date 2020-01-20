import * as React from "react";

import { ButtonLink } from "../links/ButtonLink";

interface LinkedMenuButtonProps {
  text: string;
  href: string;
}

export const LinkedMenuButton: React.FunctionComponent<LinkedMenuButtonProps> = props => (
  <ButtonLink size="large" color="inherit" href={props.href}>
    {props.text}
  </ButtonLink>
);
