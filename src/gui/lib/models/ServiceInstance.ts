import { BaseEntity } from "./BaseEntity";

export interface ServiceInstance extends BaseEntity {
  status: string;
  message?: string;
}
