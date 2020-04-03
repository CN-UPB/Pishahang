/*
 * Copyright (c) 2015 SONATA-NFV, UCL.
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

import java.util.Hashtable;

public class VimNetTable {


  private static VimNetTable myInstance = null;

  /**
   * get Singleton instance method.
   * 
   * @return the singleton instance of IpNetPool
   */
  public static VimNetTable getInstance() {
    if (myInstance == null) {
      myInstance = new VimNetTable();
    }
    return myInstance;
  }

  public static void resetInstance() {
    myInstance = null;
  }

  private Hashtable<String, IpNetPool> vimTable;

  private VimNetTable() {
    this.vimTable = new Hashtable<String, IpNetPool>();
  }

  public void deregisterVim(String vimUuid) {
    this.vimTable.remove(vimUuid);
  }

  public IpNetPool getNetPool(String vimUuid) {
    return vimTable.get(vimUuid);
  }

  public void registerVim(String vimUuid, String cidr) {
    if (this.vimTable.containsKey(vimUuid)) return;
    IpNetPool pool = new IpNetPool(cidr);
    this.vimTable.put(vimUuid, pool);
  }
}
