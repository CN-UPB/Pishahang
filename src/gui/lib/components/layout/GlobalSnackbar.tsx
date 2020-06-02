import { Snackbar } from "@material-ui/core";
import * as React from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "StoreTypes";

import { resetSnackbar } from "../../store/actions/dialogs";
import { selectSnackbarIsVisible, selectSnackbarMessage } from "../../store/selectors/dialogs";

export const GlobalSnackbar: React.FunctionComponent = () => {
  const dispatch = useDispatch();
  const isVisible = useSelector(selectSnackbarIsVisible);
  const message = useSelector(selectSnackbarMessage);

  return (
    <Snackbar
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      open={isVisible}
      autoHideDuration={8000}
      onClose={() => dispatch(resetSnackbar())}
      ContentProps={{
        "aria-describedby": "global-snackbar-message",
      }}
      message={<span id="global-snackbar-message">{message}</span>}
    />
  );
};
