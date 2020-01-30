import { Vnfd } from "./Vnfd";

export interface VnfdMetaBase {
  md5: string;
  uuid: string;
  created_at: Date;
  updated_at: Date;
  signature?: string;
  status: "active"; // TODO what else?
  username?: string;
}

export interface VmVnfdMeta extends VnfdMetaBase {
  vnfd: Vnfd;
}

export interface CnVnfdMeta extends VnfdMetaBase {
  cfd: Vnfd;
}

// TODO The separation between these two model classes is ugly. Especially when we also add FPGAs.
