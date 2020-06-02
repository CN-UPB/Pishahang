/**
 * An `ApiReply` can be used to return a `success` boolean, as well as an optional `payload` (if
 * success is true) or a `message` (otherwise) from API handler functions. This way, the return type
 * is uniform, regardless of the API call's outcome.
 */
export interface ApiReply<P = any> {
  /** Whether or not the API call succeeded */
  success: boolean;

  /** An error message (only if `success` is `false`) */
  message?: string;

  /** A payload object (only if `success` is `true`) */
  payload?: P;
}
