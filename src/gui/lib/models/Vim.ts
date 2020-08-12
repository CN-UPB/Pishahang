export enum VimType {
  OpenStack = "openstack",
  Kubernetes = "kubernetes",
  Aws = "aws",
}

/**
 * Base VIM object definition. The fields defined here are contained in data sent to the
 * API, as well as in data retrieved from the API.
 */
export interface BaseVim {
  name: string;
  country: string;
  city: string;
  type: VimType;
}

/**
 * A VIM object as handed out by the API
 */
export interface RetrievedVim extends BaseVim {
  id: string;
  coresTotal: number;
  coresUsed: number;
  memoryTotal: number;
  memoryUsed: number;
}

export interface OpenStackSpecificVimFields {
  address: string;
  tenant: {
    id: string;
    externalNetworkId: string;
    externalRouterId: string;
  };
  username: string;
  password: string;
}

export interface KubernetesSpecificVimFields {
  address: string;
  port: number;
  serviceToken: string;
  ccc: string;
}

export interface AwsSpecificVimFields {
  accessKey: string;
  secretKey: string;
}

/**
 * OpenStack VIM data as accepted by the VIM API
 */
export interface OpenStackVim extends BaseVim, OpenStackSpecificVimFields {}

/**
 * Kubernetes VIM data as accepted by the VIM API
 */
export interface KubernetesVim extends BaseVim, KubernetesSpecificVimFields {}

/**
 * AWS VIM data as accepted by the VIM API
 */
export interface AwsVim extends BaseVim, AwsSpecificVimFields {}

/**
 * A common type to represent VIM data accepted by the VIM API
 */
export type NewVim = OpenStackVim | KubernetesVim | AwsVim;
