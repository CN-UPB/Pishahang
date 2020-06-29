import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import { useSelector } from "react-redux";

import {
  selectUserEmail,
  selectUserFullName,
  selectUserIsAdmin,
} from "../../../lib/store/selectors/auth";

const UserInfoCard: React.FunctionComponent = () => {
  const userName = useSelector(selectUserFullName);
  const userEmail = useSelector(selectUserEmail);
  const isUserAdmin = useSelector(selectUserIsAdmin);

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          UserName : {userName}
        </Typography>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          Email : {userEmail}
        </Typography>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          Type : {isUserAdmin ? "Administrator" : "Non-Administrator"}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default UserInfoCard;
