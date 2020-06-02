import { BaseEntity } from "./BaseEntity";

/**
 * Services
 */
export interface Service extends BaseEntity {
  name: string;
  vendor: string;
  version: string;
}
