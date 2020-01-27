export interface User {
  username: string;
  uuid: string;
  created_at: Date;
  user_type: "developer" | "admin";
  email: string;
  last_name: string;
  first_name: string;
  instances_public_key?: string;
  instances_private_key?: string;
}
