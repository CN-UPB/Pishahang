import { IconButton, IconButtonProps } from "@material-ui/core";
import * as React from "react";

import { Link, LinkProps } from "./Link";

export type IconButtonLinkProps = IconButtonProps & LinkProps;

const InternalIconButtonLink: React.FunctionComponent<IconButtonLinkProps> = props => {
  const { innerRef, ref, underline, ...other } = props;

  return <IconButton component={Link} ref={innerRef} underline="none" {...other} />;
};

export const IconButtonLink = React.forwardRef<HTMLAnchorElement, IconButtonLinkProps>(
  (props, ref) => <InternalIconButtonLink {...props} innerRef={ref} />
);
