/*
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA, NCSR Demokritos ALL RIGHTS RESERVED.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 * 
 * Neither the name of the SONATA-NFV, UCL, NOKIA, NCSR Demokritos nor the names of its contributors
 * may be used to endorse or promote products derived from this software without specific prior
 * written permission.
 * 
 * This work has been performed in the framework of the SONATA project, funded by the European
 * Commission under Grant number 671517 through the Horizon 2020 and 5G-PPP programmes. The authors
 * would like to acknowledge the contributions of their colleagues of the SONATA partner consortium
 * (www.sonata-nfv.eu).
 *
 * @author Dario Valocchi (Ph.D.), UCL
 * 
 */

package sonata.kernel.vimadaptor.commons;

import java.util.ArrayList;
import java.util.Hashtable;

public class IpNetPool {

  private static final int[] CIDR2MASK =
      new int[] {0x00000000, 0x80000000, 0xC0000000, 0xE0000000, 0xF0000000, 0xF8000000, 0xFC000000,
          0xFE000000, 0xFF000000, 0xFF800000, 0xFFC00000, 0xFFE00000, 0xFFF00000, 0xFFF80000,
          0xFFFC0000, 0xFFFE0000, 0xFFFF0000, 0xFFFF8000, 0xFFFFC000, 0xFFFFE000, 0xFFFFF000,
          0xFFFFF800, 0xFFFFFC00, 0xFFFFFE00, 0xFFFFFF00, 0xFFFFFF80, 0xFFFFFFC0, 0xFFFFFFE0,
          0xFFFFFFF0, 0xFFFFFFF8, 0xFFFFFFFC, 0xFFFFFFFE, 0xFFFFFFFF};
  private static final String DEFAULT_CIDR = "10.0.0.0/8";
  private static final int sizeOfSubnet = 32;

  private static int getSlash(int number) {
    if (number <= 0) {
      throw new IllegalArgumentException();
    }
    return 31 - Integer.numberOfLeadingZeros(number);
  }

  private static long ipToLong(long[] ip) {

    return (ip[0] << 24) + (ip[1] << 16) + (ip[2] << 8) + ip[3];
  }

  private static String longToIp(long longIp) {
    StringBuffer sb = new StringBuffer("");
    sb.append(String.valueOf(longIp >>> 24));
    sb.append(".");
    sb.append(String.valueOf((longIp & 0x00FFFFFF) >>> 16));
    sb.append(".");
    sb.append(String.valueOf((longIp & 0x0000FFFF) >>> 8));
    sb.append(".");
    sb.append(String.valueOf(longIp & 0x000000FF));

    return sb.toString();
  }


  private ArrayList<String> freeSubnets;

  private Hashtable<String, ArrayList<String>> reservationTable;

  private Hashtable<String, String> reservedSubnets;

  /**
   * Creates an IpNetPool object.
   * 
   * @param cidr the base tenant subnet to manage in CIDR format
   */
  IpNetPool(String cidr) {
    if (cidr == null) cidr = IpNetPool.DEFAULT_CIDR;
    reservedSubnets = new Hashtable<String, String>();
    freeSubnets = new ArrayList<String>();
    reservationTable = new Hashtable<String, ArrayList<String>>();

    int slash = Integer.parseInt(cidr.split("/")[1]);
    String strAddr = cidr.split("/")[0];

    long[] addr = new long[4];

    String[] temp = strAddr.split("\\.");

    for (int i = 0; i < 4; i++) {
      addr[i] = Integer.parseInt(temp[i]);
    }

    int numberOfSubnets = (int) Math.pow(2, (32 - slash)) / sizeOfSubnet;
    long addrLong = ipToLong(addr);
    addrLong = addrLong & CIDR2MASK[slash];
    for (int i = 0; i < numberOfSubnets; i++) {
      // System.out.println(i);
      long prefixLong = addrLong + (i * sizeOfSubnet);
      // System.out.println(prefixLong);
      String stringCidr = longToIp(prefixLong) + "/" + (32 - getSlash(sizeOfSubnet));
      // System.out.println(i + " = " + stringCidr);
      this.freeSubnets.add(stringCidr);
    }

  }

  /**
   * De-allocate the subnets reserved for this service instance.
   * 
   * @param instanceUuid the uuid of instance to remove from the reservation
   */
  public void freeSubnets(String instanceUuid) throws Exception {

    ArrayList<String> subnetPool = reservationTable.get(instanceUuid);

    if (subnetPool == null) {
      throw new Exception(
          "Impossible to de-allocate. instanceUuid not present. inconsistent status.");

    }

    for (String subnet : subnetPool) {
      reservedSubnets.remove(subnet);
      freeSubnets.add(subnet);
    }
    reservationTable.remove(instanceUuid);
  }

  /**
   * Returns the number of free subnets in the tenant's address space.
   * 
   * @return an integer representing the number of subnet available in the tenant address space
   */

  public int getFreeSubnetsNumber() {
    return freeSubnets.size();
  }

  /**
   * Utilty methods that returns the first address of the given subnet.
   * 
   * @param cidr the subnet in CIDR format
   * @return the first address of the subnet, in String format.
   */
  public String getGateway(String cidr) {
    int slash = Integer.parseInt(cidr.split("/")[1]);
    String strAddr = cidr.split("/")[0];

    long[] addr = new long[4];

    String[] temp = strAddr.split("\\.");

    for (int i = 0; i < 4; i++) {
      addr[i] = Integer.parseInt(temp[i]);
    }
    long addrLong = ipToLong(addr);
    addrLong = addrLong & CIDR2MASK[slash];
    long prefixLong = addrLong + 1;
    String gateway = longToIp(prefixLong);

    return gateway;
  }

  /**
   * get a reservation from the reservation tables, if it exists.
   * 
   * @param instanceUuid the uuid of the service instance
   * 
   * @return an ArrayList of String, containing the CIDRs reserved for this service instance.
   */
  public ArrayList<String> getReservation(String instanceUuid) {
    return this.reservationTable.get(instanceUuid);
  }

  /**
   * Reserve a set of sub-nets for a given service instance.
   * 
   * @param instanceUuid the UUID of the service instance
   * @param numberOfSubnets the number of needed sub-nets
   * @return an ArrayList of string representing available CIDR
   */

  public ArrayList<String> reserveSubnets(String instanceUuid, int numberOfSubnets) {

    if (numberOfSubnets > freeSubnets.size()) {
      return null;
    }
    ArrayList<String> previousReservation = null;
    if ((previousReservation = this.reservationTable.get(instanceUuid)) != null) {
      // System.out.println("[IpNetPool] - Reservation exists for this instance. returning it");
      return previousReservation;
    }
    ArrayList<String> output = new ArrayList<String>();
    ArrayList<String> subnetPool = new ArrayList<String>();

    for (int i = 0; i < numberOfSubnets; i++) {
      String subnet = freeSubnets.remove(0);
      reservedSubnets.put(subnet, instanceUuid);
      subnetPool.add(subnet);
      output.add(subnet);
    }

    reservationTable.put(instanceUuid, subnetPool);

    return output;
  }
}
