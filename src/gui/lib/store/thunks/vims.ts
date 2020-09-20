import { RetrievedVim } from "./../../models/Vim";
import { getApiUrl } from "../../api";
import { NewVim } from "../../models/Vim";
import { ApiThunkOptions, callApiEnhanced } from "./auth";

/**
 * Return a thunk action that adds a VIM via the API
 */
export function addVim(data: NewVim, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<RetrievedVim>(
    { method: "POST", url: getApiUrl("vims"), data },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that deletes a VIM via the API
 */
export function deleteVim(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<RetrievedVim>(
    { method: "DELETE", url: getApiUrl("vims/" + id) },
    apiThunkOptions
  );
}
