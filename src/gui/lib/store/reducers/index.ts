import { combineReducers } from "redux";

import auth from "./auth";
import dialogs from "./dialogs";

// Export a root reducer that combines all the others
export default combineReducers({
  dialogs,
  auth,
});
