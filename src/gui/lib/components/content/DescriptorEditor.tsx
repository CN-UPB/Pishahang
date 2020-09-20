import "ace-builds/src-min-noconflict/ace";
import "ace-builds/src-noconflict/mode-yaml";
import "ace-builds/src-noconflict/theme-github";

import * as React from "react";
import AceEditor from "react-ace";

type Props = {
  onChange: (content: string) => any;
  value: string;
};

const textEditor: React.FunctionComponent<Props> = (props) => (
  <AceEditor
    {...props}
    mode="yaml"
    theme="github"
    name="descriptor-editor-ace"
    wrapEnabled={true}
    highlightActiveLine={true}
    fontSize={21}
    width="inherit"
    maxLines={Infinity}
  />
);

export default textEditor;
