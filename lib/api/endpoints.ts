import { Service } from "./../models/Service";
import { Descriptor } from "../models/Descriptor";
import { User } from "../models/User";

/**
 * An enumeration of API-root-relative endpoint URIs that support GET requests and return data.
 */
export enum ApiDataEndpoint {
  /**
   * Users route – returns a list of all users
   */
  Users = "users",
  Services = "services",
}

/**
 * A type map of `ApiDataEndpoint` members to their respective return data type. It is used internally by
 * the ApiDataEndpointReturnType helper type.
 */
type ApiDataEndpointReturnTypes = {
  [ApiDataEndpoint.Users]: User[];
  [ApiDataEndpoint.Services]: Service[];
};

/**
 * A helper type that maps `ApiDataEndpoint` members to the types of their respective return data
 */
export type ApiDataEndpointReturnType<
  R extends ApiDataEndpoint
> = R extends keyof ApiDataEndpointReturnTypes ? ApiDataEndpointReturnTypes[R] : any;
