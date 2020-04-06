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
  selectTableDialogContent,
} from "../../../store/selectors/dialogs";
import { KeyValueTable } from "../tables/KeyValueTable";
import { GenericDialog } from "./GenericDialog";
import { TextDialog } from "./TextDialog";

// export const GlobalInfoDialog: React.FunctionComponent = props => {
//   const dispatch = useDispatch();
//   const isVisible = useSelector(selectTableDialogContent);
//   const content = useSelector(selectTableDialogContent);
//   const title = useSelector(selectTableDialogContent);

//   return (
//     <GenericDialog
//       dialogId="table-dialog"
//       dialogTitle={}
//       open={open}
//       onClose={hideDialog}
//       buttons={
//         <>
//           <Button variant="contained" onClick={hideDialog} color="secondary" autoFocus>
//             Close
//           </Button>
//         </>
//       }
//     >
//       <KeyValueTable content={[]} />
//     </GenericDialog>
//   );
// };
