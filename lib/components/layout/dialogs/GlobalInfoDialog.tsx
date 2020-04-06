import { Button, Dialog } from "@material-ui/core";
import * as React from "react";
import { useModal } from "react-modal-hook";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "StoreTypes";

import { resetInfoDialog } from "../../../store/actions/dialogs";
import {
  selectInfoDialogIsVisible,
  selectInfoDialogMessage,
  selectInfoDialogTitle,
} from "../../../store/selectors/dialogs";
import { TextDialog } from "./TextDialog";

export const GlobalInfoDialog: React.FunctionComponent = props => {
  const dispatch = useDispatch();
  const isVisible = useSelector(selectInfoDialogIsVisible);
  const message = useSelector(selectInfoDialogMessage);
  const title = useSelector(selectInfoDialogTitle);

  return (
    <TextDialog
      dialogId="infoDialog"
      dialogTitle={title}
      dialogText={message}
      open={isVisible}
      buttons={
        <>
          <Button
            variant="contained"
            onClick={() => dispatch(resetInfoDialog())}
            color="secondary"
            autoFocus
          >
            Ok
          </Button>
        </>
      }
    ></TextDialog>
  );
};
