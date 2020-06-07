/**
 * User fields common for retrieved users and new users
 */
export interface BaseUser {
  username: string;
  fullName: string;
  email: string;
  isAdmin: boolean;
}

/**
 * User object as retrieved by the API
 */
export interface User extends BaseUser {
  id: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * User object as sent to the API when adding a new user
 */
export interface NewUser extends BaseUser {
  password: string;
}
