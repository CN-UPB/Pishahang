import * as React from "react";

export function useStateRef<S = any>(
  initialValue: S = null
): [S, React.Dispatch<React.SetStateAction<S>>, React.MutableRefObject<S>] {
  const [value, setValue] = React.useState<S>(initialValue);
  const ref = React.useRef(value);

  React.useEffect(() => {
    ref.current = value;
  }, [value]);

  return [value, setValue, ref];
}
