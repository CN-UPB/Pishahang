/**
 * Virtual network function descriptor – VM, CN, or FPGA-based
 */
export interface Descriptor {
  descriptor_version: string;
  description: string;
  name: string;
  vendor: string;
  version: string;
  author: string;
  virtual_deployment_units: any;
}
