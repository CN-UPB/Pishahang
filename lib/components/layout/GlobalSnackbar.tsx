import { Snackbar } from "@material-ui/core";

import * as React from "react";
import { connect, ConnectedProps } from "react-redux";
import { RootState } from "StoreTypes";
import { selectSnackbarMessage, selectSnackbarVisible } from "../../store/selectors/global";
import { resetSnackbar } from "../../store/actions/global";

type Props = ConnectedProps<typeof connectToRedux>;

const InternalGlobalSnackbar: React.FunctionComponent<Props> = ({ message, visible, reset }) => {
  return (
    <Snackbar
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      open={visible}
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
  visible: selectSnackbarVisible(state),
});

const mapDispatchToProps = {
  reset: resetSnackbar,
};

const connectToRedux = connect(
  mapStateToProps,
  mapDispatchToProps
);

export const GlobalSnackbar = connectToRedux(InternalGlobalSnackbar);
