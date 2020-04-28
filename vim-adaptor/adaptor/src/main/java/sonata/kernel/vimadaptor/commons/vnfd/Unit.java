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

package sonata.kernel.vimadaptor.commons.vnfd;


public interface Unit {

  public enum BandwidthUnit implements Unit {
    bps(Math.pow(10, -6)), Gbps(Math.pow(10, 3)), kbps(Math.pow(10, -3)), Mbps(1), Tbps(
        Math.pow(10, 6));

    double multiplier;

    BandwidthUnit(double multiplier) {
      this.multiplier = multiplier;
    }

    /**
     * Utility method to retrieve the multiplicative factor associated with this Bandwidth Unit (in
     * multiple or sub-multiple of the Megabit/s).
     * 
     * 
     * @return a double with the multiplicative factor.
     */
    @Override
    public double getMultiplier() {
      return this.multiplier;
    }
  }

  public enum FrequencyUnit implements Unit {
    GHz(Math.pow(10, 3)), Hz(Math.pow(10, -6)), kHz(Math.pow(10, -3)), MHz(1), THz(Math.pow(10, 6));

    double multiplier;

    FrequencyUnit(double multiplier) {
      this.multiplier = multiplier;
    }

    /**
     * Utility method to retrieve the multiplicative factor associated with this Memory Unit (in
     * multiple or sub-multiple of the MegaHertz).
     * 
     * 
     * @return a double with the multiplicative factor.
     */
    @Override
    public double getMultiplier() {
      return this.multiplier;
    }
  }

  public enum GeneralUnit implements Unit {
    percentage;

    @Override
    public double getMultiplier() {
      return 0.01;
    }
  }

  public enum MemoryUnit implements Unit {
    B(Math.pow(10, -9)), GB(1), GiB(1.074), kB(Math.pow(10, -6)), KiB(Math.pow(2, 10)), MB(
        Math.pow(10, -3)), MiB(Math.pow(2, 20)), PB(Math.pow(10, 3)), PiB(
            1.074 * Math.pow(2, 20)), TB(Math.pow(10, 3)), TiB(1.074 * Math.pow(2, 10));

    double multiplier;

    MemoryUnit(double multiplier) {
      this.multiplier = multiplier;
    }

    /**
     * Utility method to retrieve the multiplicative factor associated with this Memory Unit (in
     * multiple or sub-multiple of the GigaByte).
     * 
     * 
     * @return a double with the multiplicative factor.
     */
    @Override
    public double getMultiplier() {
      return this.multiplier;
    }
  }

  public enum TimeUnit implements Unit {
    d(3600 * 24), h(3600), m(60), ms(0.001), ns(0.000001), s(1);

    double multiplier;

    TimeUnit(double multiplier) {
      this.multiplier = multiplier;
    }

    /**
     * Utility method to retrieve the multiplicative factor associated with this Time Unit (in
     * multiple or sub-multiple of the second).
     * 
     * 
     * @return a double with the multiplicative factor.
     */
    @Override
    public double getMultiplier() {
      return this.multiplier;
    }

  }

  public double getMultiplier();
}

