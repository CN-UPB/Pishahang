import AceEditor from "react-ace";

const textEditor = props => (
  <div>
    <AceEditor
      mode={props.lan}
      theme={props.theme}
      onChange={props.onChange}
      onLoad={props.onLoad}
      defaultValue={props.defaultValue}
      value={props.value}
      name="UNIQUE_ID_OF_DIV"
      wrapEnabled={true}
      editorProps={{
        $blockScrolling: true,
      }}
      highlightActiveLine={true}
      fontSize={21}
      height="500px"
      width="500px"
    />
  </div>
);

export default textEditor;
