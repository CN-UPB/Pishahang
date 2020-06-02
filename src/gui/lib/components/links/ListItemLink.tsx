import { default as ListItem, ListItemProps } from "@material-ui/core/ListItem";
import * as React from "react";
import { Link, LinkProps } from "./Link";

export type ListItemLinkProps = ListItemProps & LinkProps;

const InternalListItemLink: React.FunctionComponent<ListItemLinkProps> = props => {
  const { innerRef, ref, children, ...other } = props;

  return (
    //@ts-ignore: Ignore errors until fix is released
    <ListItem component={Link} ref={innerRef} {...other}>
      {children}
    </ListItem>
  );
};

export const ListItemLink = React.forwardRef<HTMLAnchorElement, ListItemLinkProps>((props, ref) => (
  <InternalListItemLink {...props} innerRef={ref} />
));
