/** Vim Model */
export interface Vims {
  vimName: string;
  country: string;
  city: string;
  vimType: VimType;
  uuid: string;
  vendor: string;
  cores: string;
  memory: string;
}

export enum VimType {
  OpenStack,
  Kubernetes,
  Aws,
}
