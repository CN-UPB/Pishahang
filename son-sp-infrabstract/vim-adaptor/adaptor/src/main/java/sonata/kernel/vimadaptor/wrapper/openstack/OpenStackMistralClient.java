/*
 * Copyright (c) 2015 SONATA-NFV, UCL, NOKIA ALL RIGHTS RESERVED.
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
 * Neither the name of the SONATA-NFV, UCL, NOKIA nor the names of its contributors may be used to
 * endorse or promote products derived from this software without specific prior written permission.
 *
 * This work has been performed in the framework of the SONATA project, funded by the European
 * Commission under Grant number 671517 through the Horizon 2020 and 5G-PPP programmes. The authors
 * would like to acknowledge the contributions of their colleagues of the SONATA partner consortium
 * (www.sonata-nfv.eu).
 *
 * @author Sharon Mendel-Brin, Nokia
 */

package sonata.kernel.vimadaptor.wrapper.openstack;

import com.google.common.collect.ImmutableMap;
import com.nokia.cb.sonata.mistral.client.MistralClient;
import com.nokia.cb.sonata.mistral.client.exception.MistralHttpException;
import com.nokia.cb.sonata.mistral.client.model.Workflow;
import com.nokia.cb.sonata.mistral.client.model.WorkflowExecution;
import com.nokia.cb.sonata.mistral.client.model.WorkflowExecutionCreateRequest;

import org.apache.commons.io.IOUtils;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.net.HttpURLConnection;

/**
 * Created by smendel on 2017.
 * <p>
 * This class wraps the generic Mistral Client that supports any VIM, to be used with OpenStack
 */
public class OpenStackMistralClient {

  private static final org.slf4j.Logger Logger =
      LoggerFactory.getLogger(OpenStackMistralClient.class);

  private MistralClient mistralClient; // Mistral Client

  private String openStackUrl; // OpenStack client url

  private String password; // OpenStack Client password

  private String tenantName; // OpenStack tenant name

  private String userName; // OpenStack Client user


  public OpenStackMistralClient(String mistralIP, String openStackUrl, String userName,
      String password, String tenantName) {
    this.mistralClient = new MistralClient("http://" + mistralIP + ":8989/v2/");
    this.openStackUrl = openStackUrl;
    this.userName = userName;
    this.password = password;
    this.tenantName = tenantName;
  }

  // TODO - smendel - need to change interface to hold different count per VDU
  public String scaleStack(String stackUuid, String updatedCount) {

    Logger.info("scaleStack call for stackUuid: " + stackUuid + " updatedCount: " + updatedCount);

    String scalingResult = null;
    WorkflowExecution workflowExecution = null;

    try {
      // create workflow template
      String workflow = convertWorkflowFileToString("./YAML/scale-stack-workflow");
      // update the workflow in Mistral
      upsertWorkflow(workflow);
      WorkflowExecutionCreateRequest executionCreateRequest = new WorkflowExecutionCreateRequest();
      executionCreateRequest.setWorkflowName("scale_stack");
      executionCreateRequest.setInputs(new ImmutableMap.Builder().put("stack_name", stackUuid)
          .put("count", updatedCount).put("openstack_url", openStackUrl)
          .put("openstack_tenant_name", tenantName).put("openstack_tenant_user", userName)
          .put("openstack_tenant_password", password).build());

      Logger.info("Executing scaling workflow - calling Mistral for workflow execution");

      workflowExecution = mistralClient.workflowExecutionCreate(executionCreateRequest);
      // TODO - smendel - get scaling result, similar to whats done in
      // todo(gpaz) poling ?
      // todo(gpaz) maybe look at this example: OpenStackHeatWrapper.prepareService()

    } catch (RuntimeException e) {
      Logger.error(
          "Failed to run scaling workflow for stack: " + stackUuid + " error: " + e.getMessage());

    }

    if (workflowExecution != null) {
      // TODO -smendel - convert workflowExecution to scaling result
    }

    return scalingResult;
  }

  private String convertWorkflowFileToString(String path) throws RuntimeException {

    String template = null;

    FileInputStream inputStream = null;
    try {
      inputStream = new FileInputStream(new File(path));
    } catch (FileNotFoundException e) {
      Logger.error("Runtime error creating scaling workflow template " + e.getMessage());
      throw new RuntimeException("Could not convert workflow file to String", e);
    }

    if (inputStream != null) {
      try {
        template = IOUtils.toString(inputStream);
      } catch (IOException e) {
        Logger.error("Failed to get template from file" + e.getMessage());
        throw new RuntimeException("Could not convert workflow file to String", e);
      }
    }
    return template;
  }

  /**
   * Updates / inserts (creates) a workflow.
   * <p>
   * First try to update the workflow for performance reasons as the workflow probably already
   * exists.
   *
   * @param workflowDsl The DSL of the action
   * @return The created / updated workflow.
   */
  private Workflow upsertWorkflow(String workflowDsl) throws RuntimeException {

    Logger.info("call upsertWorkflow - update/insert Muistral workflow");

    try {
      return mistralClient.workflowUpdate(workflowDsl);
    } catch (MistralHttpException e) {
      if (e.getHttpStatus() != HttpURLConnection.HTTP_NOT_FOUND) {
        throw new RuntimeException(
            "Could not update Mistral workflow with DSL [" + workflowDsl + "]", e);
      } // else workflow does not exist - continue with creation
    }

    try {
      return mistralClient.workflowCreate(workflowDsl);

    } catch (MistralHttpException e) {
      throw new RuntimeException("Could not create Mistral workflow with DSL [" + workflowDsl + "]",
          e);
    }

  }
}
