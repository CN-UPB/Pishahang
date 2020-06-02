import { uniqueId } from "lodash";
import * as React from "react";

type ButtonProps = {
  "aria-controls": string;
  "aria-label": string;
  "aria-haspopup": boolean;
  title: string;
  onClick: (
    event: React.KeyboardEvent<HTMLButtonElement> | React.MouseEvent<HTMLButtonElement>
  ) => void;
};

type MenuProps = {
  id: string;
  keepMounted: boolean;
  open: boolean;
  anchorEl: null | Element | ((element: Element) => Element);
  getContentAnchorEl: null;
  onClose: () => void;
};

type CreateCloseHandlerFunction = (
  callback: () => void
) => (event: React.KeyboardEvent | React.MouseEvent) => void;

/**
 * A React hook for dropdown menus that returns the following utilities for menu creation:
 *
 * * `buttonProps`: An object to be spread into the button that opens the menu. Contains: `title`,
 *   `aria-controls`, `aria-haspopup`, `aria-label`, `onClick`
 *
 * * `menuProps`: An object to be spread into the `Menu` element. Contains: `id`, `keepMounted`,
 *   `open`, `anchorEl`, `getContentAnchorEl`, `onClose`
 *
 * * `createCloseHandler`: A function, that takes a function and returns an event handler that
 *   closes the menu and calls the provided function.
 *
 * @param menuButtonTitle The title used for the `title` and `aria-label` props in `buttonProps`
 */
export function useMenuHandler(
  menuButtonTitle: string
): [ButtonProps, MenuProps, CreateCloseHandlerFunction] {
  const [menuId] = React.useState(uniqueId("useMenuHandlers-"));
  const [anchorElement, setAnchorElement] = React.useState<Element | null>(null);

  const closeMenu = () => {
    setAnchorElement(null);
  };

  const buttonProps: ButtonProps = {
    "aria-controls": menuId,
    "aria-label": menuButtonTitle,
    "aria-haspopup": true,
    title: menuButtonTitle,
    onClick: event => {
      setAnchorElement(event.currentTarget);
    },
  };

  const menuProps: MenuProps = {
    id: menuId,
    keepMounted: true,
    open: Boolean(anchorElement),
    anchorEl: anchorElement,
    getContentAnchorEl: null,
    onClose: closeMenu,
  };

  const createCloseHandler: CreateCloseHandlerFunction = callback => event => {
    closeMenu();
    callback();
  };

  return [buttonProps, menuProps, createCloseHandler];
}
