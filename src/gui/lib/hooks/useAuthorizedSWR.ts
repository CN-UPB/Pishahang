import { AxiosError } from "axios";
import useSWR, { ConfigInterface, responseInterface } from "swr";

import { ApiDataEndpoint, ApiDataEndpointReturnType } from "../api/endpoints";
import { useThunkDispatch } from "../store";
import { fetchApiDataAuthorized } from "../store/thunks/auth";

export type useAuthorizedSWRResponseType<E extends ApiDataEndpoint> = responseInterface<
  ApiDataEndpointReturnType<E>,
  AxiosError
>;

/**
 * A wrapper hook around SWR that fetches data from GET API endpoints using the
 * `fetchApiDataAuthorized` thunk action.
 *
 * @param endpoint The API endpoint to fetch the data from
 * @param swrConfig An optional SWR configuration object
 */
export function useAuthorizedSWR<E extends ApiDataEndpoint>(
  endpoint: E,
  swrConfig?: ConfigInterface
): useAuthorizedSWRResponseType<E> {
  const dispatch = useThunkDispatch();
  const fetcher = (endpoint: ApiDataEndpoint) => dispatch(fetchApiDataAuthorized(endpoint));
  return useSWR(endpoint, fetcher, swrConfig);
}
