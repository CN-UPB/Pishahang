import { ListItemIcon, ListItemText } from "@material-ui/core";
import { SvgIconComponent } from "@material-ui/icons";
import * as React from "react";

import { ListItemLink } from "../links/ListItemLink";

type LinkedListItemProps = {
  text: string;
  href: string;
  icon: SvgIconComponent;
};

export const LinkedListItem: React.FunctionComponent<LinkedListItemProps> = props => (
  <ListItemLink button color="inherit" key={props.text} href={props.href}>
    <ListItemIcon>{<props.icon />}</ListItemIcon>
    <ListItemText primary={props.text} />
  </ListItemLink>
);
