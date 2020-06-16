import { AxiosError } from "axios";
import useSWR, { ConfigInterface, responseInterface } from "swr";

import { getApiUrl } from "../api";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "../api/endpoints";
import { useThunkDispatch } from "../store";
import { callApiAuthorized } from "../store/thunks/auth";

export interface useAuthorizedSWRResponseType<E extends ApiDataEndpoint>
  extends responseInterface<ApiDataEndpointReturnType<E>, AxiosError> {}

// Function override for ApiDataEndpoint type inference
export function useAuthorizedSWR<E extends ApiDataEndpoint>(
  endpoint: E,
  swrConfig?: ConfigInterface
): responseInterface<ApiDataEndpointReturnType<E>, AxiosError>;

// Function override for a URL string and manual return type specification
export function useAuthorizedSWR<DataType>(
  endpoint: string,
  swrConfig?: ConfigInterface
): responseInterface<DataType, AxiosError>;

/**
 * A wrapper hook around SWR that fetches data from GET API endpoints using the
 * `callApiAuthorized` thunk action.
 *
 * @param endpoint The API endpoint to fetch the data from (either a ApiDataEndpoint member or a URL)
 * @param swrConfig An optional SWR configuration object
 */
export function useAuthorizedSWR(endpoint: string, swrConfig?: ConfigInterface) {
  const dispatch = useThunkDispatch();
  const fetcher = (endpoint: string) =>
    dispatch(
      callApiAuthorized({
        method: "GET",
        url: getApiUrl(endpoint),
      })
    );
  return useSWR(endpoint, fetcher, swrConfig);
}
