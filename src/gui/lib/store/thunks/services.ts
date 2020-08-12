import { getApiUrl } from "../../api/index";
import { Service } from "../../models/Service";
import { ServiceInstance } from "../../models/ServiceInstance";
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
 * Return a thunk action that deletes a service
 *
 * @param id The ID of the service to be deleted
 */
export function deleteService(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<Service>(
    { method: "DELETE", url: getApiUrl("services/" + id) },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that instantiates a service
 *
 * @param id The ID of the service to be instantiated
 */
export function instantiateService(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<ServiceInstance>(
    { method: "POST", url: getApiUrl(`services/${id}/instances`) },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that terminates a service instance
 *
 * @param serviceId The ID of the service that the instance belongs to
 * @param instanceId The ID of the service instance to be terminated
 */
export function terminateServiceInstance(
  serviceId: string,
  instanceId: string,
  apiThunkOptions?: ApiThunkOptions
) {
  return callApiEnhanced<void>(
    { method: "DELETE", url: getApiUrl(`services/${serviceId}/instances/${instanceId}`) },
    apiThunkOptions
  );
}
