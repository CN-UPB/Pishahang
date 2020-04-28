# OVS-SFC 
This software implements an experimental and test version of a Networking VIM, able to receive commands from the IA to enforce SFC on a Virtual Network Service deployment.
The SFC agent is based on the use of OpenVSwitch on a Neutron Controller node, within the context of a standard OpenStack deployment. 

### Dependencies

* [OpenVSwitch](http://www.openvswitch.org/) >=2, Apache2.0

## Usage

The agent can be executed simply running the command:

    python sfc-agent.py -s x.x.x.x -i br_int -e br_ext -t br-eth

The SFC agent will use ovs-ofctl to install flow in the target server, using the specified internal(br_int) and external(br_ext) bridges used by the neutron controller, plus the bridge connected to the controller physical network interface br-eth. 

The SFC agent exposes two API calls through a UDP socket listening on default port 55555
It expects payloads formatted as JSON string, encoded in UTF-8, based on the following JSON schema:

    {
      action : String,
      in_segment : String,
      out_segment : String,
      instance_id : String, 
      port_list : [
        {
          port : String,
          order : Integer
        }
      ]
    }

* action: this field can be "add" or "delete" and is used to indicate wether the agent should create a new chain or delete an existing one.
* in_segment: CIDR (x.x.x.x/n) of the source address of the flow to be steered through the chain
* out_segment: CIDR (x.x.x.x/n) of the destination address of the flow to be steered through the chain
* instance_id: an identifier for the chain
* port: a String with the MAC address of a virtual interface
* order: an integer indicating the order of the port in the chain (starts with 0)

### Example

        ____    ____    ____
       |    |  |    |  |    |
       | F1 |  | F2 |  | F3 |
       |____|  |____|  |____|
        M1 M2   M3 M4   M5 M6
    ____|  |____|  |____|  |_____

In order to set up a chain for the function chain shown above, where M1...M6 are the MAC addresses of the six virtual interfaces, the payload will look like:

    {
      "action":"add", 
      "in_segment":"192.168.0.0/24", 
      "out_segment":"172.16.0.0/24", 
      "instance_id":"0000-00000000-00000000-0000", 
      "port_list":[
        {"port":"M1","order":0},
        {"port":"M2","order":1},
        {"port":"M3","order":2},
        {"port":"M4","order":3},
        {"port":"M5","order":4},
        {"port":"M6","order":5}
      ]
    }

In order to remove the create chain the payload will look like:

    {
      "action":"delete",
      "instance_id":"0000-00000000-00000000-0000"
    }

The agent will return a String "SUCCESS", encoded with UTF-8 charset, after a successful chain setup or delete, an error message othewise.  

## License

This Software is published under Apache 2.0 license. Please see the LICENSE file for more details.

## Useful Links

* https://www.openstack.org/ the OpenStack project homepage
* http://openvswitch.org the OpenVSwitch hompage
* http://openvswitch.org/support/dist-docs/ovs-ofctl.8.txt documentation for ovs-ofctl

#### Feedback-Channel


* You may use the mailing list [sonata-dev@lists.atosresearch.eu](mailto:sonata-dev@lists.atosresearch.eu)
* [GitHub issues](https://github.com/sonata-nfv/son-mano-framework/issues)


