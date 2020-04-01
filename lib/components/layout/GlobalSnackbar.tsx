import { Snackbar } from "@material-ui/core";
import * as React from "react";
import { ConnectedProps, connect } from "react-redux";
import { RootState } from "StoreTypes";

import { resetSnackbar } from "../../store/actions/global";
import { selectSnackbarIsVisible, selectSnackbarMessage } from "../../store/selectors/global";

type Props = ConnectedProps<typeof connectToRedux>;

const InternalGlobalSnackbar: React.FunctionComponent<Props> = ({ message, visible, reset }) => {
  return (
    <Snackbar
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      open={visible}
      autoHideDuration={8000}
      onClose={reset}
      ContentProps={{
        "aria-describedby": "global-snackbar-message",
      }}
      message={<span id="global-snackbar-message">{message}</span>}
    />
  );
};

const mapStateToProps = (state: RootState) => ({
  message: selectSnackbarMessage(state),
  visible: selectSnackbarIsVisible(state),
});

const mapDispatchToProps = {
  reset: resetSnackbar,
};

const connectToRedux = connect(mapStateToProps, mapDispatchToProps);

export const GlobalSnackbar = connectToRedux(InternalGlobalSnackbar);
