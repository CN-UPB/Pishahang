import { Button } from "@material-ui/core";
import * as React from "react";
import { useDispatch, useSelector } from "react-redux";

import { resetTableDialog } from "../../../store/actions/dialogs";
import {
  selectTableDialogContent,
  selectTableDialogIsVisible,
  selectTableDialogTitle,
} from "../../../store/selectors/dialogs";
import { KeyValueTable } from "../../content/tables/KeyValueTable";
import { GenericDialog } from "./GenericDialog";

export const GlobalTableDialog: React.FunctionComponent = () => {
  const dispatch = useDispatch();
  const title = useSelector(selectTableDialogTitle);
  const content = useSelector(selectTableDialogContent);
  const isVisible = useSelector(selectTableDialogIsVisible);

  const hideDialog = () => dispatch(resetTableDialog());

  return (
    <GenericDialog
      dialogId="table-dialog"
      dialogTitle={title}
      open={isVisible}
      onClose={hideDialog}
      buttons={
        <>
          <Button variant="contained" onClick={hideDialog} color="secondary" autoFocus>
            Close
          </Button>
        </>
      }
    >
      <KeyValueTable content={content} />
    </GenericDialog>
  );
};
