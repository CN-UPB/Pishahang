import * as React from "react";

/**
 * React hook to toggle a boolean value.
 *
 * @param initialValue The initial boolean value
 *
 * @returns [value, toggleValue]: The boolean value and a function to toggle it
 */
export function useToggle(initialValue: boolean): [boolean, () => void] {
  const [value, setValue] = React.useState(initialValue);

  const toggleValue = () => {
    setValue(!value);
  };

  return [value, toggleValue];
}
