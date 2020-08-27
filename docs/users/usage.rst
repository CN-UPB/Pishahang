**************
User Interface
**************

The user interface is divided into several different sections.
Lets get to know what each of them do.
Before we start lets dig into the concept of descriptor "Uploading" and "Onboarding". Descriptor uploading refers to the ".yaml" or ".json" descriptor file being uploaded via the user interface and is then displayed in the respective uploaded list.
Here you can edit the file, view meta information etc.
The difference between Uploading and Onboarding is just that Uploaded descriptors can be edited and onboarded multiple times with different version numbers but once onboarded those, Onboarded descriptors cannot be edited and will only allow for service instantiation.
Onboarded services are displayed as a list in the "Services" tab.

Top Bar
=======

The blue bar the top is used for ease of access to username, user profile and logout button. This functionality is always there and can be accessed from anywhere within the user interface.

Dashboard
=========

This page displays the monitoring information along with any other meta information and is always accessible via the panel on the left.

VIMs
====

This page refers to the ability to display lists of Virtual Infrastructure Managers.
All of them separated via the icons, as of now, this supports OpenStack, Kubernetes and AWS. New VIMs can be added via a small "+" icon button in the top right of the page.
For this to work, you need to provide the details for the respective VIM you want to add.
Furthermore, the VIMs list displays a wide variety of related information.
If the provided information is correct, it should go ahead and deploy a VIM and display a success message, else it will state the error, look closely to the error message there lies the clue.

OpenStack VIM Details
---------------------

Name
    Provide the Name of the VIM
Type
    Select the type from three choices OpenStack, Kubernetes or AWS.
Country
    Insert the location of the VIM (Country), e.g. DE for Germany etc.
City
    Additional location information e.g. PB for Paderborn.
Address
    Insert the IPV4 address of the VIM.
Tenant ID
    It is the project ID provided by OpenStack user interface.
Tenant External Network ID
    ID of the public network
Tenant External Router ID
    ID of the external router connected to the public network
Username
    Insert the authorized username.
Password
    Insert the associated password with the username.

Kubernetes VIM Details
----------------------

Name
    Name of the VIM.

Type
    Select Kubernetes.

Country
    Insert location information e.g. DE for Germany etc.

City
    Additional location information e.g. PB for Paderborn etc.

Host
    Kubernetes API host address.

Port
    Kubernetes API port of the provided host.

Service Token
    Can be obtained by running ``microk8s kubectl describe secret`` on the Kubernetes host.

Cluster CA Certificate
    Can be obtained by running the command below on the Kubernetes host.
      
    .. code-block:: bash

        kubectl get secret -o jsonpath="{.items[?(@.type==\"kubernetes.io/service-account-token\")].data['ca\.crt']}"

AWS VIM Details
---------------

Name
    Provide a name for the VIM.
Type
    Select AWS from the list.
Country
    Provide location information.
City
    Provide additional location information.
Access Key
    Insert the provided access key.
Secret Key
    Insert the provided secret key.

Service Descriptors
===================

Displays a list of "Uploaded" Service descriptors along with some details more of which are accessible through the information icon button to the right of each service descriptor. There is an upload button in the top right corner of the descriptors list. This can be used to upload a descriptor file and is common across some of the other pages. There are four buttons in each descriptor list item defined below.

Red - Stacked Plus Icon 
    This is for service onboarding, clicking this should go ahead and onboard a service, given that the respective function descriptors are uploaded.

Blue - Info Icon
    View meta information about the respective service. A dialog will appear with the resulting information.
 
Green - Pen Icon
    Displays a dialog with descriptor information inside already converted into ".yaml" and this information is ready to be "edited". Take care about what you edit here, as the respective function descriptors may also need to be edited. After editing you can save this information and this will be saved via the gatekeeper.

Orange - Trash Icon
    Deletes the respective descriptor from the gatekeeper and the updates the user interface.

Function Descriptors
====================

Contains a small list of supported platforms. As of now it will expand to display three options, OpenStack, Kubernetes and AWS.

OpenStack
    Contains a list of OS uploaded ".vnfd" descriptors. New descriptors can be uploaded via the Blue upload button at the top. Supported descriptor file mime type are ".yaml" and ".json". After uploading the descriptor will be displayed along with some actions "info", "edit" and "delete".

Kubernetes
    Contains a list of K8s uploaded .cnfd descriptors. New descriptors can be uploaded via the blue upload button also supports ".yaml" and ".json" mime types. After uploading the descriptor will be displayed along with some actions "info", "edit" and "delete".

AWS
    Contains a list of uploaded descriptors. New ones can be uploaded via the same process as before. After successful upload, the information will be displayed in the list along with the same action buttons, "info", "edit" and "delete".
 
Services
    After clicking the onboard icon in the "Service Descriptors" listed descriptors, the respective "Onboarded" services will be displayed here, these services are ready to be "Instantiated". From the listed services, there will be some actions defined in detail below.
 
Blue 
    Info icon: Displays the extended information dialog. 
  
Green
    Play icon: Goes ahead and starts the process of service instantiation. The information is displayed under the respective onboarded descriptor list item.

Red
    Delete icon: Goes ahead and terminates the service.

Monitoring
==========

This displays a list of plugins and their states. Moreover against each plugin there are a few buttons which allow the user to control the states described below.

Blue - Info icon
    Displays meta information about the plugin.

Blue - Pause/Play icon
    Places the plugin in a running or temporary paused state.

Red - Power icon
    Stops or Starts the respective plugin.

Users
=====

(Admins Only) - displays a list of users for user management. The page contains a "+" plus icon the top to allow for additional users to be created. A new user will be displayed once the requested information is provided.
