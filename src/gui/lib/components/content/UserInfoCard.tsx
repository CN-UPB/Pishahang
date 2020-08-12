import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import { useSelector } from "react-redux";

import {
  selectUserCreatedAt,
  selectUserEmail,
  selectUserFullName,
  selectUserId,
  selectUserIsAdmin,
  selectUserUpdatedAt,
} from "../../../lib/store/selectors/auth";

const UserInfoCard: React.FunctionComponent = () => {
  const userName = useSelector(selectUserFullName);
  const userEmail = useSelector(selectUserEmail);
  const isUserAdmin = useSelector(selectUserIsAdmin);
  const userId = useSelector(selectUserId);
  const userCreatedAt = useSelector(selectUserCreatedAt);
  const userUpdatedAt = useSelector(selectUserUpdatedAt);

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography>UserName : {userName}</Typography>
        <Typography>Email : {userEmail}</Typography>
        <Typography>Type : {isUserAdmin ? "Administrator" : "Non-Administrator"}</Typography>
        <Typography>Id : {userId}</Typography>
        <Typography>CreatedAt : {userCreatedAt}</Typography>
        <Typography>UpdatedAt : {userUpdatedAt}</Typography>
      </CardContent>
    </Card>
  );
};

export default UserInfoCard;
