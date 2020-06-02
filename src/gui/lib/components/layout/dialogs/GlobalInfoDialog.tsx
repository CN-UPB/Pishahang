import { Button } from "@material-ui/core";
import * as React from "react";
import { useDispatch, useSelector } from "react-redux";

import { resetInfoDialog } from "../../../store/actions/dialogs";
import {
  selectInfoDialogIsVisible,
  selectInfoDialogMessage,
  selectInfoDialogTitle,
} from "../../../store/selectors/dialogs";
import { TextDialog } from "./TextDialog";

export const GlobalInfoDialog: React.FunctionComponent = props => {
  const dispatch = useDispatch();
  const title = useSelector(selectInfoDialogTitle);
  const message = useSelector(selectInfoDialogMessage);
  const isVisible = useSelector(selectInfoDialogIsVisible);

  const hideDialog = () => dispatch(resetInfoDialog());

  return (
    <TextDialog
      dialogId="info-dialog"
      dialogTitle={title}
      dialogText={message}
      open={isVisible}
      onClose={hideDialog}
      buttons={
        <>
          <Button variant="contained" onClick={hideDialog} color="secondary" autoFocus>
            Ok
          </Button>
        </>
      }
    ></TextDialog>
  );
};
