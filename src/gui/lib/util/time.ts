/**
 * Given an ISO-8601-compliant date string, returns a user-friendly localized string representation
 * of the provided date.
 *
 * @param isoDate The ISO-8601-compliant date string to be formatted
 */
export function formatDate(isoDate: string) {
  return new Date(Date.parse(isoDate)).toLocaleString();
}

/**
 * Returns the current UNIX timestamp
 */
export function getTimestamp() {
  return Math.round(Date.now() / 1000);
}
