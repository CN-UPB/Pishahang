import { AxiosError } from "axios";
import { useDispatch, useSelector } from "react-redux";
import useSWR, { ConfigInterface, responseInterface } from "swr";

import { NullTokenError, fetchApiDataAuthorized } from "../api/auth";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "../api/endpoints";
import { authError } from "../store/actions/auth";
import { selectAccessToken } from "../store/selectors/auth";

export type useAuthorizedSWRResponseType<E extends ApiDataEndpoint> = responseInterface<
  ApiDataEndpointReturnType<E>,
  AxiosError | NullTokenError
>;

/**
 * A wrapper hook around SWR that fetches data from GET API endpoints using
 * `fetchApiDataAuthorized`. It gets the auth token using the react-redux `useSelector` hook and
 * dispatches an `authError` action if the authentication fails.
 *
 * @param endpoint The API endpoint to fetch the data from
 * @param swrConfig An optional SWR configuration object
 */
export function useAuthorizedSWR<E extends ApiDataEndpoint>(
  endpoint: E,
  swrConfig?: ConfigInterface
): useAuthorizedSWRResponseType<E> {
  const token = useSelector(selectAccessToken);
  const dispatch = useDispatch();

  const fetcher = (endpoint: E, token: string) =>
    fetchApiDataAuthorized(endpoint, token, () => dispatch(authError()));

  return useSWR([endpoint, token], fetcher, swrConfig);
}
