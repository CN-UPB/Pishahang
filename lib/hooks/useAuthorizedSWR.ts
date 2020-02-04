import { useDispatch, useSelector } from "react-redux";
import useSWR, { ConfigInterface } from "swr";

import { fetchApiDataAuthorized } from "../api/auth";
import { authError } from "../store/actions/auth";
import { selectAuthToken } from "../store/selectors/auth";

/**
 * A wrapper hook around SWR that fetches data using `fetchApiDataAuthorized`. It gets the auth
 * token using the react-redux `useSelector` hook and dispatches an `authError` action when the
 * authentication fails.
 *
 * @param endpoint The API-root-relative resource URI to be fetched
 * @param swrConfig An optional SWR configuration object (where the `fetcher` key will be ignored)
 */
export function useAuthorizedSWR(endpoint: string, swrConfig?: ConfigInterface) {
  const token = useSelector(selectAuthToken);
  const dispatch = useDispatch();

  const fetcher = (endpoint: string, token: string) =>
    fetchApiDataAuthorized(endpoint, token, () => dispatch(authError()));

  return useSWR([endpoint, token], fetcher, swrConfig);
}
