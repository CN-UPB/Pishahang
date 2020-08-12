import { getApiUrl } from "../../api";
import { Plugin, PluginState } from "../../models/Plugin";
import { ApiThunkOptions, callApiEnhanced } from "./auth";

/**
 * Return a thunk action that retrieves information on a specific plugin via the API
 */
export function getPlugin(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<Plugin>(
    { method: "GET", url: getApiUrl("plugins/" + id) },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that stops a specific plugin via the API
 */
export function stopPlugin(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<Plugin>(
    { method: "DELETE", url: getApiUrl("plugins/" + id) },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that changes the lifecycle state of a specific plugin via the API
 */
export function changePluginLifecycleState(
  id: string,
  targetState: PluginState,
  apiThunkOptions?: ApiThunkOptions
) {
  return callApiEnhanced<Plugin>(
    {
      method: "PUT",
      url: getApiUrl("plugins/" + id + "/lifecycle"),
      data: { targetState: targetState === PluginState.RUNNING ? "start" : "pause" },
    },
    apiThunkOptions
  );
}
