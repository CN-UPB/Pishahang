import { Descriptor } from "./Descriptor";
import { DescriptorType } from "./descriptorType";

export interface DescriptorMeta {
  id: string;
  type: DescriptorType;
  createdAt: string;
  updatedAt: string;
  descriptor: Descriptor;
}
