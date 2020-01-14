import global from "./global";
import user from "./user";
import { combineReducers } from "redux";

// Export a root reducer that combines all the others
export default combineReducers({
  global,
  user,
});
