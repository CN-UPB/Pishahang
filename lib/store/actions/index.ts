import * as GlobalActions from "./global";
import * as UserActions from "./user";

// Export all actions for usage in type definitions
export default {
  global: GlobalActions,
  owner: UserActions,
};
