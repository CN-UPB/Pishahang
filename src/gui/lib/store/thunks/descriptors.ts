import yaml from "js-yaml";

import { getApiUrl } from "../../api/index";
import { Descriptor } from "../../models/Descriptor";
import { DescriptorContent } from "../../models/Descriptor";
import { DescriptorType } from "../../models/Descriptor";
import { callApiEnhanced } from "./auth";
import { ApiThunkOptions } from "./auth";

/**
 * Return a thunk action that uploads a descriptor via the API
 */
export function uploadDescriptor(
  type: DescriptorType,
  contentString: string,
  apiThunkOptions?: ApiThunkOptions
) {
  return callApiEnhanced<Descriptor>(
    {
      method: "POST",
      url: getApiUrl("descriptors"),
      data: { content: yaml.safeLoad(contentString) as DescriptorContent, contentString, type },
    },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that fetches a descriptor based on the given id
 */
export function getDescriptor(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<Descriptor>(
    { method: "GET", url: getApiUrl("descriptors/" + id) },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that deletes a descriptor by its id
 */
export function deleteDescriptor(id: string, apiThunkOptions?: ApiThunkOptions) {
  return callApiEnhanced<Descriptor>(
    { method: "DELETE", url: getApiUrl("descriptors/" + id) },
    apiThunkOptions
  );
}

/**
 * Return a thunk action that updates a descriptor with the given id
 */
export function updateDescriptor(
  id: string,
  contentString: string,
  apiThunkOptions?: ApiThunkOptions
) {
  return callApiEnhanced<Descriptor>(
    {
      method: "PUT",
      url: getApiUrl("descriptors/" + id),
      data: { content: yaml.safeLoad(contentString) as DescriptorContent, contentString },
    },
    apiThunkOptions
  );
}
