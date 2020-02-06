import { cosdService } from "./cosdService";

/**
 * http://131.234.29.248/api/v2/complex-services?status=active&limit=10&offset=0
 * Complex Services
 */
export interface Service {
  created_at: Date;
  md5: string;
  signature: string;
  /** status of service */
  status: string;
  updated_at: Date;
  username: string;
  uuid: string;
  cosd: cosdService;
}
