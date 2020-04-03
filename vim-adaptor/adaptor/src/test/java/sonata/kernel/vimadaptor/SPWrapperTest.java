/*
 * Copyright (c) 2015 SONATA-NFV, UCL, OPT ALL RIGHTS RESERVED.
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
 * @author Xose Ramon Sousa, OPT
 * @author Santiago Rodriguez, OPT
 * 
 */

package sonata.kernel.vimadaptor;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.util.Arrays;
import java.util.Properties;
import javax.ws.rs.NotAuthorizedException;

import org.json.JSONObject;
import org.json.JSONTokener;
import org.junit.Assert;
import org.junit.Before;
import org.junit.FixMethodOrder;
import org.junit.Test;
import org.slf4j.LoggerFactory;
import org.junit.runners.MethodSorters;
import sonata.kernel.vimadaptor.commons.FunctionDeployResponse;
import sonata.kernel.vimadaptor.commons.ServiceRecord;
import sonata.kernel.vimadaptor.commons.Status;
import sonata.kernel.vimadaptor.commons.VduRecord;
import sonata.kernel.vimadaptor.commons.VimResources;
import sonata.kernel.vimadaptor.commons.VnfRecord;
import sonata.kernel.vimadaptor.commons.VnfcInstance;
import sonata.kernel.vimadaptor.commons.nsd.ServiceDescriptor;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.wrapper.ResourceUtilisation;
import sonata.kernel.vimadaptor.wrapper.SonataGkMockedClient;
import sonata.kernel.vimadaptor.wrapper.WrapperConfiguration;
import sonata.kernel.vimadaptor.wrapper.WrapperType;
import sonata.kernel.vimadaptor.wrapper.sp.client.SonataGkClient;
import sonata.kernel.vimadaptor.wrapper.sp.client.model.GkRequestStatus;
import sonata.kernel.vimadaptor.wrapper.sp.client.model.GkServiceListEntry;

@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class SPWrapperTest {

	private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(SPWrapperTest.class);

	private Properties sonataProperties;
	private static final String SONATA_CONFIG_FILEPATH = "/etc/son-mano/sonata.config";
	private static final String SONATA_2ND_SP_ADDRESS = "sonata_2nd_sp_address";
	private static final String MOCKED_2ND_PLATFORM = "mocked_2nd_platform";
	private static final String VENDOR = "eu.sonata-nfv";
	private static final String NAME = "vtu-vnf";
	private static final String VERSION = "0.5";

	private WrapperConfiguration config;
	
	static String instanceUuid;

	@Before
	public void setUp() {
		System.setProperty("org.apache.commons.logging.Log", "org.apache.commons.logging.impl.SimpleLog");
		System.setProperty("org.apache.commons.logging.simplelog.showdatetime", "false");
		System.setProperty("org.apache.commons.logging.simplelog.log.httpclient.wire.header", "warn");
		System.setProperty("org.apache.commons.logging.simplelog.log.org.apache.commons.httpclient", "warn");

		this.sonataProperties = parseConfigFile();

		config = new WrapperConfiguration();

		config.setAuthUserName("sonata");
		config.setAuthPass("1234");
		config.setUuid("1234-1234-1234-1234");
		config.setVimEndpoint(this.sonataProperties.getProperty(SONATA_2ND_SP_ADDRESS));
		config.setWrapperType(WrapperType.COMPUTE);
	}

	@Test
	public void test1_GetResourceUtilisation() {

		Logger.info("<<<<<<<<<<<<<<<<<<<<<<  getResourceUtilisation Test  >>>>>>>>>>>>>>>>>>>>>>>>");

		String[] vim_cities = { "Athens", "Aveiro-Beach", "Aveiro", "London", "Paderborn", "Tel Aviv" };
		boolean lowerSPIsMocked = Boolean.parseBoolean(this.sonataProperties.getProperty(MOCKED_2ND_PLATFORM));
		Logger.info("lowerSPIsMocked: "+lowerSPIsMocked);

		Logger.info("[SpWrapperTest] Reading config files");
		Assert.assertNotNull(this.sonataProperties.getProperty(SONATA_2ND_SP_ADDRESS));

		Logger.info("[SpWrapperTest] Creating SONATA Rest Client");
		Object client;
		if (lowerSPIsMocked) {
			client = new SonataGkMockedClient();
		} else {
			client = new SonataGkClient(config.getVimEndpoint(), config.getAuthUserName(), config.getAuthPass());
		}

		Logger.info("[SpWrapperTest] Retrieving VIMs connected to slave SONATA SP");
		VimResources[] lvims = {};

		try {

			if (Boolean.parseBoolean(this.sonataProperties.getProperty(MOCKED_2ND_PLATFORM))) {
				Logger.info("[SpWrapperTest] Using a mocked GK");
				lvims = ((SonataGkMockedClient) client).getVims();
			} else {
				Logger.info("[SpWrapperTest] Using a real GK");
				if (!((SonataGkClient) client).authenticate())
					throw new NotAuthorizedException("Client cannot login to the SP");

				lvims = ((SonataGkClient) client).getVims();
			}
		} catch (IOException e) {
			Logger.error("Error retrieving the vims list: " + e.getMessage());
		}

		Logger.info("[SpWrapperTest] VIMs list size: " + lvims.length);

		// mocked vim list must contains 5 elements
		Assert.assertTrue(lvims.length != 0);

		// mocked vim list contains the vim_cities
		for (int i = 0; i < lvims.length; i++) {
			Assert.assertTrue(Arrays.asList(vim_cities).contains(lvims[i].getVimCity()));
		}

		ResourceUtilisation ru = new ResourceUtilisation();

		ru.setTotCores(0);
		ru.setTotMemory(0);
		ru.setUsedCores(0);
		ru.setUsedMemory(0);

		for (VimResources res : lvims) {
			ru.setTotCores(ru.getTotCores() + res.getCoreTotal());
			ru.setUsedCores(ru.getUsedCores() + res.getCoreUsed());
			ru.setTotMemory(ru.getTotMemory() + res.getMemoryTotal());
			ru.setUsedMemory(ru.getUsedMemory() + res.getMemoryUsed());
		}

		Assert.assertTrue(ru.getTotCores() > 0);
		Assert.assertTrue(ru.getUsedCores() > 0);
		Assert.assertTrue(ru.getTotMemory() > 0);
		Assert.assertTrue(ru.getUsedMemory() > 0);

		Logger.info("Response created");
	}

	@Test
	public void test2_DeployFunction() {

		Logger.info("<<<<<<<<<<<<<<<<<<<<<<  deployFunction Test  >>>>>>>>>>>>>>>>>>>>>>>>");

		Logger.info("[SpWrapperTest] Creating SONATA Rest Client");
		Object gkClient;
		boolean lowerSPIsMocked = Boolean.parseBoolean(this.sonataProperties.getProperty(MOCKED_2ND_PLATFORM));

		if (lowerSPIsMocked) {
			gkClient = new SonataGkMockedClient();
		} else {
			gkClient = new SonataGkClient(config.getVimEndpoint(), config.getAuthUserName(), config.getAuthPass());

			Logger.info("[SpWrapperTest] Authenticating SONATA Rest Client");
			if (!((SonataGkClient) gkClient).authenticate())
				throw new NotAuthorizedException("Client cannot login to the SP");
		}

		GkServiceListEntry[] availableNsds = null;
		try {
			if (lowerSPIsMocked) {
				availableNsds = ((SonataGkMockedClient) gkClient).getServices();
			} else {
				availableNsds = ((SonataGkClient) gkClient).getServices();
			}
		} catch (IOException e1) {
			Logger.error("unable to contact the GK to check the available services list");
			return;
		}

		Assert.assertTrue(availableNsds.length > 0);

		String serviceUuid = null;
		VnfDescriptor vnfd = new VnfDescriptor();

		vnfd.setVendor(VENDOR);
		vnfd.setName(NAME);
		vnfd.setVersion(VERSION);

		Logger.debug("VNF: " + vnfd.getVendor() + "::" + vnfd.getName() + "::" + vnfd.getVersion());
		for (GkServiceListEntry serviceEntry : availableNsds) {
			ServiceDescriptor nsd = serviceEntry.getNsd();
			Logger.debug("Checking NSD:");
			Logger.debug(nsd.getVendor() + "::" + nsd.getName() + "::" + nsd.getVersion());
			boolean matchingVendor = nsd.getVendor().equals(vnfd.getVendor());
			boolean matchingName = nsd.getName().equals(vnfd.getName());
			boolean matchingVersion = nsd.getVersion().equals(vnfd.getVersion());
			Logger.debug("Matches: " + matchingVendor + "::" + matchingName + "::" + matchingVersion);
			boolean matchingCondition = matchingVendor && matchingName && matchingVersion;
			if (matchingCondition) {
				serviceUuid = serviceEntry.getUuid();
				break;
			}
		}

		Assert.assertNotNull(serviceUuid);
		
		// - sending a REST call to the underlying SP Gatekeeper for service
		// deployment
		String requestUuid = null;
		Logger.debug("Sending NSD instantiation request to GK...");
		try {
			if (lowerSPIsMocked) {
				requestUuid = ((SonataGkMockedClient) gkClient).instantiateService(serviceUuid);
			} else {
				requestUuid = ((SonataGkClient) gkClient).instantiateService(serviceUuid);
			}
		} catch (Exception e) {
			Logger.error(e.getMessage());
			Assert.assertNotNull(requestUuid);
			return;
		}

		Assert.assertNotNull(requestUuid);
		// - than poll the GK until the status is "READY" or "ERROR"

		int counter = 0;
		int wait = 1000;
		int maxCounter = 50;
		int maxWait = 15000;
		String status = null;
		while ((status == null || !status.equals("READY") || !status.equals("ERROR")) && counter < maxCounter) {
			try {
				if (lowerSPIsMocked) {
					status = ((SonataGkMockedClient) gkClient).getRequestStatus(requestUuid);
				} else {
					status = ((SonataGkClient) gkClient).getRequestStatus(requestUuid);
				}
			} catch (IOException e1) {
				Logger.error("Error while retrieving the Service instantiation request status. Trying again in "
						+ (wait / 1000) + " seconds");
			}
			Logger.info("Status of request" + requestUuid + ": " + status);
			if (status != null && (status.equals("READY") || status.equals("ERROR"))) {
				break;
			}
			try {
				Thread.sleep(wait);
			} catch (InterruptedException e) {
				Logger.error(e.getMessage(), e);
			}
			counter++;
			wait = Math.min(wait * 2, maxWait);

		}

		if (status == null) {
			Logger.error("Unable to contact the GK to check the service instantiation status");
			return;
		}
		if (status.equals("ERROR")) {
			Logger.error("Service instantiation failed on the other SP side.");
			return;
		}

		Assert.assertNotEquals(status, "ERROR");
		Assert.assertNotNull(status);
		Assert.assertTrue("READY".equalsIgnoreCase(status));

		// Get NSR to retrieve VNFR_ID

		GkRequestStatus instantiationRequest = null;
		try {
			if (lowerSPIsMocked) {
				instantiationRequest = ((SonataGkMockedClient) gkClient).getRequest(requestUuid);
			} else {
				instantiationRequest = ((SonataGkClient) gkClient).getRequest(requestUuid);
			}
		} catch (IOException e) {
			Logger.error("Service instantiation failed. Can't retrieve instantiation request status.");
			return;
		}

		Assert.assertNotNull(instantiationRequest);
		
		instanceUuid = instantiationRequest.getServiceInstanceUuid();
		Assert.assertNotNull(instanceUuid);

		ServiceRecord nsr = null;
		try {
			if (lowerSPIsMocked) {
				nsr = ((SonataGkMockedClient) gkClient).getNsr(instantiationRequest.getServiceInstanceUuid());
			} else {
				nsr = ((SonataGkClient) gkClient).getNsr(instantiationRequest.getServiceInstanceUuid());
			}
		} catch (IOException e1) {			
			Logger.error("Service instantiation failed. Can't retrieve NSR of instantiated service with service instance uuid: "+instantiationRequest.getServiceInstanceUuid());
			Assert.assertNotNull(nsr);
		}

		Assert.assertNotNull(nsr);

		// Get VNFR
		// There will be just one VNFR referenced by this NSR
		String vnfrId = nsr.getNetworkFunctions().get(0).getVnfrId();
		VnfRecord remoteVnfr = null;
		try {
			if (lowerSPIsMocked) {
				remoteVnfr = ((SonataGkMockedClient) gkClient).getVnfr(vnfrId);
			} else {
				remoteVnfr = ((SonataGkClient) gkClient).getVnfr(vnfrId);
			}
		} catch (IOException e1) {
			Logger.error("Service instantiation failed. Can't retrieve VNFR of instantiated function with uuid: "+vnfrId);
			Assert.assertNotNull(remoteVnfr);
		}

		Assert.assertNotNull(remoteVnfr);

		// Map VNFR field to stripped VNFR.
		FunctionDeployResponse response = new FunctionDeployResponse();
		response.setRequestStatus("COMPLETED");
		response.setInstanceVimUuid("");
		response.setInstanceName("");
		response.setVimUuid(config.getUuid());
		response.setMessage("");

		VnfRecord vnfr = new VnfRecord();
		vnfr.setDescriptorVersion("vnfr-schema-01");
		vnfr.setId(vnfd.getInstanceUuid());
		vnfr.setDescriptorReference(vnfd.getUuid());
		vnfr.setStatus(Status.offline);

		vnfr.setVirtualDeploymentUnits(remoteVnfr.getVirtualDeploymentUnits());

		for (VduRecord vdur : vnfr.getVirtualDeploymentUnits()) {
			for (VnfcInstance vnfc : vdur.getVnfcInstance()) {
				vnfc.setVimId("1111-2222-3333-4444");
			}
		}

		// Send the response back
		response.setVnfr(vnfr);

		Logger.info("Response created");

	}

	@Test
	public void test3_RemoveService() {

		Logger.info("<<<<<<<<<<<<<<<<<<<<<<  removeService Test  >>>>>>>>>>>>>>>>>>>>>>>>");
		
		Logger.info("[SpWrapper] Creating SONATA Rest Client");
		
		Object gkClient;
		boolean lowerSPIsMocked = Boolean.parseBoolean(this.sonataProperties.getProperty(MOCKED_2ND_PLATFORM));
		
		if (lowerSPIsMocked) {
			gkClient = new SonataGkMockedClient();
		} else {
			gkClient = new SonataGkClient(config.getVimEndpoint(), config.getAuthUserName(), config.getAuthPass());

			Logger.info("[SpWrapperTest] Authenticating SONATA Rest Client");
			if (!((SonataGkClient) gkClient).authenticate())
				throw new NotAuthorizedException("Client cannot login to the SP");
		}

		String requestUuid = null;
		try {
			if (lowerSPIsMocked) {
				requestUuid = ((SonataGkMockedClient) gkClient).removeServiceInstance(instanceUuid);
			} else {
				requestUuid = ((SonataGkClient) gkClient).removeServiceInstance(instanceUuid);
			}			
		} catch (Exception e) {
			Logger.error(e.getMessage(), e);
		}
		
		Assert.assertNotNull(requestUuid);

		// - than poll the GK until the status is "READY" or "ERROR"

		int counter = 0;
		int wait = 1000;
		int maxCounter = 50;
		int maxWait = 15000;
		String status = null;
		while ((status == null || !status.equals("READY") || !status.equals("ERROR")) && counter < maxCounter) {
			try {				
				if (lowerSPIsMocked) {
					status = ((SonataGkMockedClient) gkClient).getRequestStatus(requestUuid);
				} else {
					status = ((SonataGkClient) gkClient).getRequestStatus(requestUuid);
				}
			} catch (IOException e1) {
				Logger.error(e1.getMessage(), e1);
				Logger.error("Error while retrieving the Service termination request status. Trying again in "
						+ (wait / 1000) + " seconds");
			}
			Logger.info("Status of request " + requestUuid + ": " + status);
			if (status != null && (status.equals("READY") || status.equals("ERROR"))) {
				break;
			}
			try {
				Thread.sleep(wait);
			} catch (InterruptedException e) {
				Logger.error(e.getMessage(), e);
			}
			counter++;
			wait = Math.min(wait * 2, maxWait);

		}
		
		Assert.assertNotNull(status);
		Assert.assertTrue(!status.equals("ERROR"));
		Assert.assertTrue(status.equals("READY"));

		Logger.info("Response created");
	}

	private static Properties parseConfigFile() {
		Logger.debug("Parsing sonata.config conf file");
		Properties prop = new Properties();
		try {
			InputStreamReader in = new InputStreamReader(new FileInputStream(SONATA_CONFIG_FILEPATH),
					Charset.forName("UTF-8"));

			JSONTokener tokener = new JSONTokener(in);

			JSONObject jsonObject = (JSONObject) tokener.nextValue();

			String gk2Host = jsonObject.getString(SONATA_2ND_SP_ADDRESS);
			prop.put(SONATA_2ND_SP_ADDRESS, gk2Host);
			String isMocked = jsonObject.getString(MOCKED_2ND_PLATFORM);
			prop.put(MOCKED_2ND_PLATFORM, isMocked);
			Logger.info("is 2nd platform mocked? - "+isMocked);

		} catch (FileNotFoundException e) {
			Logger.error("Unable to load Sonata Config file", e);
			System.exit(1);
		}
		Logger.debug("sonata.config conf file parsed");
		return prop;
	}
}
