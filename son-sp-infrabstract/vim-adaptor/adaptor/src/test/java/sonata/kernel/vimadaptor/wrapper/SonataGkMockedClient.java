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

package sonata.kernel.vimadaptor.wrapper;

import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.databind.ObjectMapper;

import sonata.kernel.vimadaptor.commons.ServiceRecord;
import sonata.kernel.vimadaptor.commons.SonataManifestMapper;
import sonata.kernel.vimadaptor.commons.VimResources;
import sonata.kernel.vimadaptor.commons.VnfRecord;
import sonata.kernel.vimadaptor.commons.vnfd.VnfDescriptor;
import sonata.kernel.vimadaptor.wrapper.sp.client.model.GkRequestStatus;
import sonata.kernel.vimadaptor.wrapper.sp.client.model.GkServiceListEntry;

public class SonataGkMockedClient {
	
	private static final org.slf4j.Logger Logger = LoggerFactory.getLogger(SonataGkMockedClient.class);

	/**
	 * @return a List of VimResource object taken from file
	 * @throws IOException
	 *             for JSON parsing error
	 */
	public VimResources[] getVims() throws IOException {

		JSONParser parser = new JSONParser();
		Object object;

		try {
			object = parser.parse(new FileReader("./JSON/vims-list.json"));
		} catch (ParseException e) {
			throw new IOException("Error parsing vim list.");
		}
		
		Logger.info("object: "+object.toString());
		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		VimResources[] list = mapper.readValue(object.toString(), VimResources[].class);

		return list;

	}

	/**
	 * @return an ArrayList of ServiceDescriptor object taken from file
	 * @throws IOException
	 *             for JSON parsing error
	 */
	public GkServiceListEntry[] getServices() throws IOException {

		JSONParser parser = new JSONParser();
		Object object;

		Logger.info("Reading Service list file");
		
		try {
			object = parser.parse(new FileReader("./JSON/services-list.json"));
		} catch (ParseException e) {
			throw new IOException("Error parsing service list.");
		}
		
		Logger.info(object.toString());

		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();

	    GkServiceListEntry[] list =
	        mapper.readValue(object.toString(), GkServiceListEntry[].class);

		return list;
	}
	
	/**
	 * @return an ArrayList of VnfDescriptor object taken from file
	 * @throws IOException
	 *             for JSON parsing error
	 */
	public ArrayList<VnfDescriptor> getFunctions() throws IOException {

		JSONParser parser = new JSONParser();
		Object object;

		try {
			object = parser.parse(new FileReader("./JSON/functions-list.json"));
		} catch (ParseException e) {
			throw new IOException("Error parsing service list.");
		}

		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		VnfDescriptor[] list = mapper.readValue(object.toString(), VnfDescriptor[].class);
		ArrayList<VnfDescriptor> descList = new ArrayList<VnfDescriptor>(Arrays.asList(list));

		return descList;
	}

	/**
	 * @param serviceUuid
	 *            the uuid of the NSD to be instantiated
	 * @return a String representing the generated request UUID
	 * @throws IOException
	 *             for http client error or JSON parsing error
	 */
	public String instantiateService(String serviceUuid) throws IOException {

		JSONParser parser = new JSONParser();
		Object object;
		try {
			object = parser.parse(new FileReader("./JSON/request-response.json"));
		} catch (ParseException e1) {
			throw new IOException("Error parsing request response.");
		}

		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		GkRequestStatus requestObject = mapper.readValue(object.toString(), GkRequestStatus.class);

		return requestObject.getId();
	}
	
	/**
	 * @param serviceUuid
	 *            the uuid of the NSR to be terminated
	 * @return a String representing the generated request UUID
	 * @throws IOException
	 *             for http client error or JSON parsing error
	 */
	public String removeServiceInstance(String serviceUuid) throws IOException {

		JSONParser parser = new JSONParser();
		Object object;
		try {
			object = parser.parse(new FileReader("./JSON/request-response.json"));
		} catch (ParseException e1) {
			throw new IOException("Error parsing request response.");
		}

		String body =
		        String.format("{\"service_instance_uuid\": \"%s\", \"request_type\":\"TERMINATE\"}", serviceUuid);
		Logger.debug(body);
		
		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		GkRequestStatus requestObject = mapper.readValue(object.toString(), GkRequestStatus.class);

		return requestObject.getId();
	}	

	/**
	 * @param requestUuid
	 *            uuid of the GK request
	 * @return a String representing the status of the request
	 * @throws IOException
	 *             for http client error or JSON parsing error
	 */
	public String getRequestStatus(String requestUuid) throws IOException {
		JSONParser parser = new JSONParser();
		Object object;
		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		GkRequestStatus requestRequestObject = new GkRequestStatus();
		
		try {
			object = parser.parse(new FileReader("./JSON/request.json"));
			requestRequestObject = mapper.readValue(object.toString(), GkRequestStatus.class);
		} catch (Exception e1) {
			Logger.error("Error parsing request response."+e1);
		}

		Logger.info("---------- "+requestRequestObject.getStatus());
		return requestRequestObject.getStatus();
	}

	/**
	 * @param requestUuid
	 *            the UUID of the request
	 * @return a RequestObject that contains information on the request
	 * @throws IOException
	 *             for http client error or JSON parsing error
	 */
	public GkRequestStatus getRequest(String requestUuid) throws IOException {
		JSONParser parser = new JSONParser();
		Object object;
		try {
			object = parser.parse(new FileReader("./JSON/request-response.json"));
		} catch (ParseException e1) {
			throw new IOException("Error parsing request response.");
		}

		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		GkRequestStatus requestObject = mapper.readValue(object.toString(), GkRequestStatus.class);

		return requestObject;
	}

	/**
	 * @param serviceInstanceUuid
	 *            the UUID of the service instance
	 * @return the ServiceRecord associated with this service instance
	 * @throws IOException
	 *             for http client error or JSON parsing error
	 *
	 */
	public ServiceRecord getNsr(String serviceInstanceUuid) throws IOException {
		JSONParser parser = new JSONParser();
		Object object;
		try {
			object = parser.parse(new FileReader("./JSON/service-record.json"));
		} catch (ParseException e1) {
			throw new IOException("Error parsing request response.");
		}

		Logger.info(object.toString());
		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		ServiceRecord nsr = mapper.readValue(object.toString(), ServiceRecord.class);

		return nsr;
	}

	/**
	 * @param vnfrId
	 *            the ID of the VNFR to retrieve
	 * @return the VnfRecord object for the specified VNFR ID
	 * @throws IOException
	 *             for http client error or JSON parsing error
	 */
	public VnfRecord getVnfr(String vnfrId) throws IOException {
		JSONParser parser = new JSONParser();
		Object object;
		try {
			object = parser.parse(new FileReader("./JSON/function-record.json"));
		} catch (ParseException e1) {
			throw new IOException("Error parsing request response.");
		}

		ObjectMapper mapper = SonataManifestMapper.getSonataJsonMapper();
		VnfRecord vnfr = mapper.readValue(object.toString(), VnfRecord.class);
		
		return vnfr;
	}
}
