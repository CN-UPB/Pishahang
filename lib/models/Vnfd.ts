/**
 * Virtual network function descriptor – VM, CN, or FPGA-based
 */
export interface Vnfd {
  descriptor_version: string;
  description: string;
  name: string;
  vendor: string;
  version: string;
  author: string;
  virtual_deployment_units: any;
}
