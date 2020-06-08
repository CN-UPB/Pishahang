import { BaseEntity } from "./BaseEntity";
/**
 * User fields common for retrieved users and "local" users
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
export interface User extends BaseUser, BaseEntity {}

/**
 * User object as sent to the API when adding or modifying a new user
 */
export interface LocalUser extends BaseUser {
  password: string;
}
