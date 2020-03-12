import { Descriptor } from "./Descriptor";
import { DescriptorType } from "./DescriptorType";

export interface DescriptorMeta {
  id: string;
  type: DescriptorType;
  createdAt: string;
  updatedAt: string;
  descriptor: Descriptor;
}
