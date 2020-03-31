import { AxiosError } from "axios";
import { useDispatch, useSelector } from "react-redux";
import useSWR, { ConfigInterface } from "swr";

import { NullTokenError, fetchApiDataAuthorized } from "../api/auth";
import { ApiDataEndpoint, ApiDataEndpointReturnType } from "../api/endpoints";
import { authError } from "../store/actions/auth";
import { selectAccessToken } from "../store/selectors/auth";

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
) {
  const token = useSelector(selectAccessToken);
  const dispatch = useDispatch();

  const fetcher = (endpoint: E, token: string) =>
    fetchApiDataAuthorized(endpoint, token, () => dispatch(authError()));

  return useSWR<ApiDataEndpointReturnType<E>, AxiosError | NullTokenError>(
    [endpoint, token],
    fetcher,
    swrConfig
  );
}
