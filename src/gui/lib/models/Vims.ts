export enum VimType {
  OpenStack = "openStack",
  Kubernetes = "kubernetes",
  Aws = "aws",
}

export interface Vim {
  coreTotal: string;
  coreUsed: string;
  memoryTotal: string;
  memoryUsed: string;
  vimCity: string;
  vimDomain: string;
  vimEndpoint: string;
  vimName: string;
  vimType: string;
  vimUuid: string;
}
