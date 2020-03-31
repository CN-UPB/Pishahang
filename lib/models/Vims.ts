export enum VimType {
  OpenStack = "openStack",
  Kubernetes = "kubernetes",
  Aws = "aws",
}

/** Vim Model */
export interface Vim {
  vimName: string;
  country: string;
  city: string;
  vimType: VimType;
  uuid: string;
  vendor: string;
  cores: string;
  memory: string;
}
