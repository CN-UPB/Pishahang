export enum VimType {
  OpenStack = "openstack",
  Kubernetes = "kubernetes",
  Aws = "aws",
}

export interface Vim {
  id: string;
  name: string;
  country: string;
  city: string;
  type: VimType;
  coresTotal: number;
  coresUsed: number;
  memoryTotal: number;
  memoryUsed: number;
}
