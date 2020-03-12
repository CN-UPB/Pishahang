import { cosdService } from "./cosdService";
import { DescriptorType } from "./DescriptorType";

/**
 * http://131.234.29.248/api/v2/complex-services?status=active&limit=10&offset=0
 * Complex Services
 */
export interface Service {
  type: DescriptorType;
  createdAt: string;
  updatedAt: string;
  id: string;
  descriptor: cosdService;
}
