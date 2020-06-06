import { getApiUrl } from "../../api/index";
import { Service } from "../../models/Service";
import { ApiThunkOptions, callApiEnhanced } from "./auth";

/**
 * Return a thunk action that onboards a service descriptor
 *
 * @param id The ID of the service descriptor to be onboarded
 */
export function onboardServiceDescriptor(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<Service>(
    { method: "POST", url: getApiUrl("services"), data: { id } },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that instantiates a service
 *
 * @param id The ID of the service to be instantiated
 */
export function instantiateService(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<Service>(
    { method: "POST", url: getApiUrl(`services/${id}/instances`) },
    apiThunkOptions
  );
}
