import { DescriptorType } from "./descriptorType";
import { Vnfd } from "./Vnfd";

export interface VnfdMeta {
  id: string;
  type: DescriptorType;
  descriptor: Vnfd;
}
