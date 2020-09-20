import { blue, pink } from "@material-ui/core/colors";
import { createMuiTheme } from "@material-ui/core/styles";

const theme = createMuiTheme({
  palette: {
    primary: blue,
    secondary: pink,
    background: {
      default: "#fff",
    },
  },
  props: {
    MuiTextField: {
      variant: "standard",
      fullWidth: true,
    },
  },
});

export default theme;
