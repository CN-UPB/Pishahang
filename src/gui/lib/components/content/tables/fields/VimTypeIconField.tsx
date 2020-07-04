import { Tooltip } from "@material-ui/core";
import * as React from "react";

import { VimType } from "../../../../models/Vim";

type Props = {
  /**
   * The service instance to render the status field for
   */
  vimType: VimType;
};

export const VimTypeIconField: React.FunctionComponent<Props> = ({ vimType }) => {
  return (
    <div style={{ alignItems: "center" }}>
      <Tooltip title={vimType}>
        <img src={`/img/icons/${vimType}.svg`} style={{ maxHeight: "24px" }} />
      </Tooltip>
    </div>
  );
};
