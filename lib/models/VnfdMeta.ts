import { Vnfd } from "./Vnfd";

export interface VnfdMeta {
  md5: string;
  uuid: string;
  created_at: Date;
  updated_at: Date;
  signature?: string;
  status: "active"; // TODO what else?
  username?: string;
  descriptor: Vnfd;
}
