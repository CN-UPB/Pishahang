import { default as Button, ButtonProps } from "@material-ui/core/Button";
import * as React from "react";
import { Link, LinkProps } from "./Link";

export type ButtonLinkProps = ButtonProps & LinkProps;

const InternalButtonLink: React.FunctionComponent<ButtonLinkProps> = props => {
  const { innerRef, ref, underline, ...other } = props;

  return <Button component={Link} ref={innerRef} underline="none" {...other} />;
};

export const ButtonLink = React.forwardRef<HTMLAnchorElement, ButtonLinkProps>((props, ref) => (
  <InternalButtonLink {...props} innerRef={ref} />
));
