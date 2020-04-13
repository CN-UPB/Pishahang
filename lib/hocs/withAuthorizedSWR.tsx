import { CircularProgress } from "@material-ui/core";
import * as React from "react";
import { Subtract } from "utility-types";

import { ApiDataEndpoint } from "../api/endpoints";
import { useAuthorizedSWR, useAuthorizedSWRResponseType } from "../hooks/useAuthorizedSWR";

export type InjectedAuthorizedSWRProps<E extends ApiDataEndpoint> = Omit<
  useAuthorizedSWRResponseType<E>,
  "data" | "error"
> &
  Required<Pick<useAuthorizedSWRResponseType<E>, "data">>;

/**
 * A HOC that takes an `endpoint` parameter and uses `useAuthorizedSWR` with that endpoint
 * internally. As long as `useAuthorizedSWR` returns no `data` or `error`, a loading spinner is
 * rendered. Otherwise, the wrapped component is rendered and the return data of `useAuthorizedSWR`
 * is injected (as specified in the `InjectedAuthorizedSWRProps` type).
 *
 * @param Component The component to be rendered with the injected SWR properties
 *                  (`InjectedAuthorizedSWRProps`)
 */
export const withAuthorizedSWR = <
  P extends InjectedAuthorizedSWRProps<E>,
  E extends ApiDataEndpoint
>(
  endpoint: E
) => (
  Component: React.ComponentType<P>
): React.FunctionComponent<Subtract<P, InjectedAuthorizedSWRProps<E>>> => (props) => {
  const { data, error, ...swrProps } = useAuthorizedSWR(endpoint);

  if (!data || error) {
    return (
      <CircularProgress
        color="secondary"
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
        }}
      />
    );
  } else {
    return <Component {...(props as P)} data={data} />;
  }
};
