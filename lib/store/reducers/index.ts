import { combineReducers } from "redux";

import auth from "./auth";
import global from "./global";

// Export a root reducer that combines all the others
export default combineReducers({
  global,
  auth,
});
