/**
* Copyright 2017 Telefónica Investigación y Desarrollo, S.A.U.
* This file is part of openmano
* All Rights Reserved.
*
* Licensed under the Apache License, Version 2.0 (the "License"); you may
* not use this file except in compliance with the License. You may obtain
* a copy of the License at
*
*         http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
* License for the specific language governing permissions and limitations
* under the License.
*
* For those usages not covered by the Apache License, Version 2.0 please
* contact with: nfvlabs@tid.es
**/

-- MySQL dump 10.13  Distrib 5.7.20, for Linux (x86_64)
--
-- Host: localhost    Database: {{mano_db}}
-- ------------------------------------------------------
-- Server version	5.7.20-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `{{mano_db}}`
--

/*!40000 DROP DATABASE IF EXISTS `{{mano_db}}`*/;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `{{mano_db}}` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `{{mano_db}}`;

--
-- Table structure for table `datacenter_nets`
--

DROP TABLE IF EXISTS `datacenter_nets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datacenter_nets` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `vim_net_id` varchar(36) NOT NULL,
  `datacenter_id` varchar(36) NOT NULL,
  `type` enum('bridge','data','ptp') NOT NULL DEFAULT 'data' COMMENT 'Type of network',
  `multipoint` enum('true','false') NOT NULL DEFAULT 'true',
  `shared` enum('true','false') NOT NULL DEFAULT 'false' COMMENT 'If can be shared with serveral scenarios',
  `description` varchar(255) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `name_datacenter_id` (`name`,`datacenter_id`),
  KEY `FK_datacenter_nets_datacenters` (`datacenter_id`),
  CONSTRAINT `FK_datacenter_nets_datacenters` FOREIGN KEY (`datacenter_id`) REFERENCES `datacenters` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Contain the external nets of a datacenter';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `datacenter_tenants`
--

DROP TABLE IF EXISTS `datacenter_tenants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datacenter_tenants` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `datacenter_id` varchar(36) NOT NULL COMMENT 'Datacenter of this tenant',
  `vim_tenant_name` varchar(256) DEFAULT NULL,
  `vim_tenant_id` varchar(256) DEFAULT NULL COMMENT 'Tenant ID at VIM',
  `created` enum('true','false') NOT NULL DEFAULT 'false' COMMENT 'Indicates if this tenant has been created by openmano, or it existed on VIM',
  `user` varchar(64) DEFAULT NULL,
  `passwd` varchar(64) DEFAULT NULL,
  `config` varchar(4000) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  KEY `FK_vim_tenants_datacenters` (`datacenter_id`),
  CONSTRAINT `FK_vim_tenants_datacenters` FOREIGN KEY (`datacenter_id`) REFERENCES `datacenters` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Scenarios defined by the user';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `datacenters`
--

DROP TABLE IF EXISTS `datacenters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datacenters` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `type` varchar(36) NOT NULL DEFAULT 'openvim',
  `vim_url` varchar(150) NOT NULL COMMENT 'URL of the VIM for the REST API',
  `vim_url_admin` varchar(150) DEFAULT NULL,
  `config` varchar(4000) DEFAULT NULL COMMENT 'extra config information in json',
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Datacenters managed by the NFVO.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `datacenters_flavors`
--

DROP TABLE IF EXISTS `datacenters_flavors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datacenters_flavors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flavor_id` varchar(36) NOT NULL,
  `datacenter_vim_id` varchar(36) NOT NULL,
  `vim_id` varchar(36) NOT NULL,
  `status` enum('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
  `vim_info` text,
  `created` enum('true','false') NOT NULL DEFAULT 'false' COMMENT 'Indicates if it has been created by openmano, or already existed',
  `extended` varchar(2000) DEFAULT NULL COMMENT 'Extra description json format of additional devices',
  PRIMARY KEY (`id`),
  KEY `FK__flavors` (`flavor_id`),
  KEY `FK_datacenters_flavors_datacenter_tenants` (`datacenter_vim_id`),
  CONSTRAINT `FK__flavors` FOREIGN KEY (`flavor_id`) REFERENCES `flavors` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_datacenters_flavors_datacenter_tenants` FOREIGN KEY (`datacenter_vim_id`) REFERENCES `datacenter_tenants` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `datacenters_images`
--

DROP TABLE IF EXISTS `datacenters_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `datacenters_images` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `image_id` varchar(36) NOT NULL,
  `datacenter_vim_id` varchar(36) NOT NULL,
  `vim_id` varchar(36) NOT NULL,
  `status` enum('ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
  `vim_info` text,
  `created` enum('true','false') NOT NULL DEFAULT 'false' COMMENT 'Indicates if it has been created by openmano, or already existed',
  PRIMARY KEY (`id`),
  KEY `FK__images` (`image_id`),
  KEY `FK_datacenters_images_datacenter_tenants` (`datacenter_vim_id`),
  CONSTRAINT `FK__images` FOREIGN KEY (`image_id`) REFERENCES `images` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_datacenters_images_datacenter_tenants` FOREIGN KEY (`datacenter_vim_id`) REFERENCES `datacenter_tenants` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `flavors`
--

DROP TABLE IF EXISTS `flavors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flavors` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `disk` smallint(5) unsigned DEFAULT NULL,
  `ram` mediumint(7) unsigned DEFAULT NULL,
  `vcpus` smallint(5) unsigned DEFAULT NULL,
  `extended` varchar(2000) DEFAULT NULL COMMENT 'Extra description json format of needed resources and pining, orginized in sets per numa',
  PRIMARY KEY (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `images` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `universal_name` varchar(255) DEFAULT NULL,
  `checksum` varchar(32) DEFAULT NULL,
  `location` varchar(200) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `metadata` varchar(2000) DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `location` (`location`),
  UNIQUE KEY `universal_name_checksum` (`universal_name`,`checksum`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instance_actions`
--

DROP TABLE IF EXISTS `instance_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instance_actions` (
  `uuid` varchar(36) NOT NULL,
  `tenant_id` varchar(36) DEFAULT NULL,
  `instance_id` varchar(36) DEFAULT NULL,
  `description` varchar(64) DEFAULT NULL COMMENT 'CREATE, DELETE, SCALE OUT/IN, ...',
  `number_tasks` smallint(6) NOT NULL DEFAULT '1',
  `number_done` smallint(6) NOT NULL DEFAULT '0',
  `number_failed` smallint(6) NOT NULL DEFAULT '0',
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  KEY `FK_actions_tenants` (`tenant_id`),
  CONSTRAINT `FK_actions_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `nfvo_tenants` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Contains client actions over instances';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instance_interfaces`
--

DROP TABLE IF EXISTS `instance_interfaces`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instance_interfaces` (
  `uuid` varchar(36) NOT NULL,
  `instance_vm_id` varchar(36) NOT NULL,
  `instance_net_id` varchar(36) NOT NULL,
  `interface_id` varchar(36) DEFAULT NULL,
  `vim_interface_id` varchar(128) DEFAULT NULL,
  `mac_address` varchar(32) DEFAULT NULL,
  `ip_address` varchar(64) DEFAULT NULL,
  `vim_info` text,
  `type` enum('internal','external') NOT NULL COMMENT 'Indicates if this interface is external to a vnf, or internal',
  `floating_ip` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Indicates if a floating_ip must be associated to this interface',
  `port_security` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'Indicates if port security must be enabled or disabled. By default it is enabled',
  `sdn_port_id` varchar(36) DEFAULT NULL COMMENT 'Port id in ovim',
  `compute_node` varchar(100) DEFAULT NULL COMMENT 'Compute node id used to specify the SDN port mapping',
  `pci` varchar(50) DEFAULT NULL COMMENT 'PCI of the  physical port in the host',
  `vlan` smallint(5) unsigned DEFAULT NULL COMMENT 'VLAN tag used by the port',
  PRIMARY KEY (`uuid`),
  KEY `FK_instance_vms` (`instance_vm_id`),
  KEY `FK_instance_nets` (`instance_net_id`),
  KEY `FK_instance_ids` (`interface_id`),
  CONSTRAINT `FK_instance_ids` FOREIGN KEY (`interface_id`) REFERENCES `interfaces` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `FK_instance_nets` FOREIGN KEY (`instance_net_id`) REFERENCES `instance_nets` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_instance_vms` FOREIGN KEY (`instance_vm_id`) REFERENCES `instance_vms` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Table with all running associattion among VM instances and net instances';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instance_nets`
--

DROP TABLE IF EXISTS `instance_nets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instance_nets` (
  `uuid` varchar(36) NOT NULL,
  `vim_net_id` varchar(128) DEFAULT NULL,
  `instance_scenario_id` varchar(36) DEFAULT NULL,
  `sce_net_id` varchar(36) DEFAULT NULL,
  `net_id` varchar(36) DEFAULT NULL,
  `datacenter_id` varchar(36) DEFAULT NULL,
  `datacenter_tenant_id` varchar(36) NOT NULL,
  `status` enum('ACTIVE','INACTIVE','DOWN','BUILD','ERROR','VIM_ERROR','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
  `error_msg` varchar(1024) DEFAULT NULL,
  `vim_info` text,
  `multipoint` enum('true','false') NOT NULL DEFAULT 'true',
  `created` enum('true','false') NOT NULL DEFAULT 'false' COMMENT 'Created or already exists at VIM',
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `sdn_net_id` varchar(36) DEFAULT NULL COMMENT 'Network id in ovim',
  PRIMARY KEY (`uuid`),
  KEY `FK_instance_nets_instance_scenarios` (`instance_scenario_id`),
  KEY `FK_instance_nets_sce_nets` (`sce_net_id`),
  KEY `FK_instance_nets_nets` (`net_id`),
  KEY `FK_instance_nets_datacenters` (`datacenter_id`),
  KEY `FK_instance_nets_datacenter_tenants` (`datacenter_tenant_id`),
  CONSTRAINT `FK_instance_nets_datacenter_tenants` FOREIGN KEY (`datacenter_tenant_id`) REFERENCES `datacenter_tenants` (`uuid`),
  CONSTRAINT `FK_instance_nets_datacenters` FOREIGN KEY (`datacenter_id`) REFERENCES `datacenters` (`uuid`),
  CONSTRAINT `FK_instance_nets_instance_scenarios` FOREIGN KEY (`instance_scenario_id`) REFERENCES `instance_scenarios` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_instance_nets_nets` FOREIGN KEY (`net_id`) REFERENCES `nets` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `FK_instance_nets_sce_nets` FOREIGN KEY (`sce_net_id`) REFERENCES `sce_nets` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Instances of networks';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instance_scenarios`
--

DROP TABLE IF EXISTS `instance_scenarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instance_scenarios` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `tenant_id` varchar(36) DEFAULT NULL,
  `scenario_id` varchar(36) DEFAULT NULL,
  `datacenter_id` varchar(36) NOT NULL,
  `datacenter_tenant_id` varchar(36) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `cloud_config` mediumtext,
  PRIMARY KEY (`uuid`),
  KEY `FK_scenarios_nfvo_tenants` (`tenant_id`),
  KEY `FK_instance_scenarios_vim_tenants` (`datacenter_tenant_id`),
  KEY `FK_instance_scenarios_datacenters` (`datacenter_id`),
  KEY `FK_instance_scenarios_scenarios` (`scenario_id`),
  CONSTRAINT `FK_instance_scenarios_datacenter_tenants` FOREIGN KEY (`datacenter_tenant_id`) REFERENCES `datacenter_tenants` (`uuid`),
  CONSTRAINT `FK_instance_scenarios_datacenters` FOREIGN KEY (`datacenter_id`) REFERENCES `datacenters` (`uuid`),
  CONSTRAINT `FK_instance_scenarios_nfvo_tenants` FOREIGN KEY (`tenant_id`) REFERENCES `nfvo_tenants` (`uuid`),
  CONSTRAINT `FK_instance_scenarios_scenarios` FOREIGN KEY (`scenario_id`) REFERENCES `scenarios` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Instances of scenarios defined by the user';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instance_vms`
--

DROP TABLE IF EXISTS `instance_vms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instance_vms` (
  `uuid` varchar(36) NOT NULL,
  `instance_vnf_id` varchar(36) NOT NULL,
  `vm_id` varchar(36) DEFAULT NULL,
  `vim_vm_id` varchar(128) DEFAULT NULL,
  `status` enum('ACTIVE:NoMgmtIP','ACTIVE','INACTIVE','BUILD','ERROR','VIM_ERROR','PAUSED','SUSPENDED','DELETED','SCHEDULED_CREATION','SCHEDULED_DELETION') NOT NULL DEFAULT 'BUILD',
  `error_msg` varchar(1024) DEFAULT NULL,
  `vim_info` text,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `vim_vm_id` (`vim_vm_id`),
  KEY `FK_instance_vms_vms` (`vm_id`),
  KEY `FK_instance_vms_instance_vnfs` (`instance_vnf_id`),
  CONSTRAINT `FK_instance_vms_instance_vnfs` FOREIGN KEY (`instance_vnf_id`) REFERENCES `instance_vnfs` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_instance_vms_vms` FOREIGN KEY (`vm_id`) REFERENCES `vms` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Instances of VMs as part of VNF instances';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instance_vnfs`
--

DROP TABLE IF EXISTS `instance_vnfs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instance_vnfs` (
  `uuid` varchar(36) NOT NULL,
  `instance_scenario_id` varchar(36) NOT NULL,
  `vnf_id` varchar(36) NOT NULL,
  `sce_vnf_id` varchar(36) DEFAULT NULL,
  `datacenter_id` varchar(36) DEFAULT NULL,
  `datacenter_tenant_id` varchar(36) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  KEY `FK_instance_vnfs_vnfs` (`vnf_id`),
  KEY `FK_instance_vnfs_instance_scenarios` (`instance_scenario_id`),
  KEY `FK_instance_vnfs_sce_vnfs` (`sce_vnf_id`),
  KEY `FK_instance_vnfs_datacenters` (`datacenter_id`),
  KEY `FK_instance_vnfs_datacenter_tenants` (`datacenter_tenant_id`),
  CONSTRAINT `FK_instance_vnfs_datacenter_tenants` FOREIGN KEY (`datacenter_tenant_id`) REFERENCES `datacenter_tenants` (`uuid`),
  CONSTRAINT `FK_instance_vnfs_datacenters` FOREIGN KEY (`datacenter_id`) REFERENCES `datacenters` (`uuid`),
  CONSTRAINT `FK_instance_vnfs_instance_scenarios` FOREIGN KEY (`instance_scenario_id`) REFERENCES `instance_scenarios` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_instance_vnfs_sce_vnfs` FOREIGN KEY (`sce_vnf_id`) REFERENCES `sce_vnfs` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `FK_instance_vnfs_vnfs` FOREIGN KEY (`vnf_id`) REFERENCES `vnfs` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Instances of VNFs as part of a scenario';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `interfaces`
--

DROP TABLE IF EXISTS `interfaces`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `interfaces` (
  `uuid` varchar(36) NOT NULL,
  `internal_name` varchar(255) NOT NULL,
  `external_name` varchar(255) DEFAULT NULL,
  `vm_id` varchar(36) NOT NULL,
  `net_id` varchar(36) DEFAULT NULL,
  `type` enum('mgmt','bridge','data') NOT NULL DEFAULT 'data' COMMENT 'Type of network',
  `vpci` char(12) DEFAULT NULL,
  `bw` mediumint(8) unsigned DEFAULT NULL COMMENT 'BW expressed in Mbits/s. Maybe this field is not necessary.',
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `model` varchar(12) DEFAULT NULL,
  `mac` char(18) DEFAULT NULL,
  `ip_address` varchar(64) DEFAULT NULL,
  `floating_ip` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Indicates if a floating_ip must be associated to this interface',
  `port_security` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'Indicates if port security must be enabled or disabled. By default it is enabled',
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `internal_name_vm_id` (`internal_name`,`vm_id`),
  KEY `FK_interfaces_vms` (`vm_id`),
  KEY `FK_interfaces_nets` (`net_id`),
  CONSTRAINT `FK_interfaces_nets` FOREIGN KEY (`net_id`) REFERENCES `nets` (`uuid`) ON DELETE CASCADE,
  CONSTRAINT `FK_interfaces_vms` FOREIGN KEY (`vm_id`) REFERENCES `vms` (`uuid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='VM interfaces';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ip_profiles`
--

DROP TABLE IF EXISTS `ip_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ip_profiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `net_id` varchar(36) DEFAULT NULL,
  `sce_net_id` varchar(36) DEFAULT NULL,
  `instance_net_id` varchar(36) DEFAULT NULL,
  `ip_version` enum('IPv4','IPv6') NOT NULL DEFAULT 'IPv4',
  `subnet_address` varchar(64) DEFAULT NULL,
  `gateway_address` varchar(64) DEFAULT NULL,
  `dns_address` varchar(255) DEFAULT NULL COMMENT 'dns ip list separated by semicolon',
  `dhcp_enabled` enum('true','false') NOT NULL DEFAULT 'true',
  `dhcp_start_address` varchar(64) DEFAULT NULL,
  `dhcp_count` int(11) DEFAULT NULL,
  `security_group` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_ipprofiles_nets` (`net_id`),
  KEY `FK_ipprofiles_scenets` (`sce_net_id`),
  KEY `FK_ipprofiles_instancenets` (`instance_net_id`),
  CONSTRAINT `FK_ipprofiles_instancenets` FOREIGN KEY (`instance_net_id`) REFERENCES `instance_nets` (`uuid`) ON DELETE CASCADE,
  CONSTRAINT `FK_ipprofiles_nets` FOREIGN KEY (`net_id`) REFERENCES `nets` (`uuid`) ON DELETE CASCADE,
  CONSTRAINT `FK_ipprofiles_scenets` FOREIGN KEY (`sce_net_id`) REFERENCES `sce_nets` (`uuid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Table containing the IP parameters of a network, either a net, a sce_net or and instance_net.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logs`
--

DROP TABLE IF EXISTS `logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logs` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `nfvo_tenant_id` varchar(36) DEFAULT NULL,
  `related` varchar(36) NOT NULL COMMENT 'Relevant element for the log',
  `uuid` varchar(36) DEFAULT NULL COMMENT 'Uuid of vnf, scenario, etc. that log relates to',
  `level` enum('panic','error','info','debug','verbose') NOT NULL,
  `description` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3423 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nets`
--

DROP TABLE IF EXISTS `nets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nets` (
  `uuid` varchar(36) NOT NULL,
  `vnf_id` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `type` enum('bridge','data','ptp') NOT NULL DEFAULT 'data' COMMENT 'Type of network',
  `multipoint` enum('true','false') NOT NULL DEFAULT 'false',
  `description` varchar(255) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `vnf_id_name` (`vnf_id`,`name`),
  CONSTRAINT `FK_nets_vnfs` FOREIGN KEY (`vnf_id`) REFERENCES `vnfs` (`uuid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Networks in a VNF definition. These are only the internal networks among VMs of the same VNF.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfvo_tenants`
--

DROP TABLE IF EXISTS `nfvo_tenants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfvo_tenants` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `encrypted_RO_priv_key` varchar(2000) DEFAULT NULL,
  `RO_pub_key` varchar(510) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Scenarios defined by the user';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sce_interfaces`
--

DROP TABLE IF EXISTS `sce_interfaces`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sce_interfaces` (
  `uuid` varchar(36) NOT NULL,
  `sce_vnf_id` varchar(36) NOT NULL,
  `sce_net_id` varchar(36) DEFAULT NULL,
  `interface_id` varchar(36) DEFAULT NULL,
  `ip_address` varchar(64) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  KEY `FK_sce_interfaces_sce_vnfs` (`sce_vnf_id`),
  KEY `FK_sce_interfaces_sce_nets` (`sce_net_id`),
  KEY `FK_sce_interfaces_interfaces` (`interface_id`),
  CONSTRAINT `FK_sce_interfaces_interfaces` FOREIGN KEY (`interface_id`) REFERENCES `interfaces` (`uuid`),
  CONSTRAINT `FK_sce_interfaces_sce_nets` FOREIGN KEY (`sce_net_id`) REFERENCES `sce_nets` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_sce_interfaces_sce_vnfs` FOREIGN KEY (`sce_vnf_id`) REFERENCES `sce_vnfs` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='VNF interfaces in a scenario definition.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sce_nets`
--

DROP TABLE IF EXISTS `sce_nets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sce_nets` (
  `uuid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `scenario_id` varchar(36) DEFAULT NULL COMMENT 'NULL if net is matched to several scenarios',
  `type` enum('bridge','data','ptp') NOT NULL DEFAULT 'data' COMMENT 'Type of network',
  `multipoint` enum('true','false') NOT NULL DEFAULT 'true',
  `external` enum('true','false') NOT NULL DEFAULT 'false' COMMENT 'If external, net is already present at VIM',
  `description` varchar(255) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `graph` varchar(2000) DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  KEY `FK_sce_nets_scenarios` (`scenario_id`),
  CONSTRAINT `FK_sce_nets_scenarios` FOREIGN KEY (`scenario_id`) REFERENCES `scenarios` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Networks in a scenario definition. It only considers networks among VNFs. Networks among internal VMs are only considered in tble ''nets''.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sce_vnfs`
--

DROP TABLE IF EXISTS `sce_vnfs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sce_vnfs` (
  `uuid` varchar(36) NOT NULL,
  `member_vnf_index` smallint(6) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `scenario_id` varchar(36) NOT NULL,
  `vnf_id` varchar(36) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `graph` varchar(2000) DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `name_scenario_id` (`name`,`scenario_id`),
  KEY `FK_sce_vnfs_scenarios` (`scenario_id`),
  KEY `FK_sce_vnfs_vnfs` (`vnf_id`),
  CONSTRAINT `FK_sce_vnfs_scenarios` FOREIGN KEY (`scenario_id`) REFERENCES `scenarios` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_sce_vnfs_vnfs` FOREIGN KEY (`vnf_id`) REFERENCES `vnfs` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='VNFs in scenario definitions. This table also contains the Physical Network Functions and the external elements such as MAN, Core, etc.\r\n';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scenarios`
--

DROP TABLE IF EXISTS `scenarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scenarios` (
  `uuid` varchar(36) NOT NULL,
  `osm_id` varchar(255) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `short_name` varchar(255) DEFAULT NULL,
  `tenant_id` varchar(36) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `vendor` varchar(255) DEFAULT NULL,
  `public` enum('true','false') NOT NULL DEFAULT 'false',
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `descriptor` text COMMENT 'Original text descriptor used for create the scenario',
  `cloud_config` mediumtext,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `osm_id_tenant_id` (`osm_id`,`tenant_id`),
  KEY `FK_scenarios_nfvo_tenants` (`tenant_id`),
  CONSTRAINT `FK_scenarios_nfvo_tenants` FOREIGN KEY (`tenant_id`) REFERENCES `nfvo_tenants` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Scenarios defined by the user';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `schema_version`
--

DROP TABLE IF EXISTS `schema_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schema_version` (
  `version_int` int(11) NOT NULL COMMENT 'version as a number. Must not contain gaps',
  `version` varchar(20) NOT NULL COMMENT 'version as a text',
  `openmano_ver` varchar(20) NOT NULL COMMENT 'openmano version',
  `comments` varchar(2000) DEFAULT NULL COMMENT 'changes to database',
  `date` date DEFAULT NULL,
  PRIMARY KEY (`version_int`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='database schema control version';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tenants_datacenters`
--

DROP TABLE IF EXISTS `tenants_datacenters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tenants_datacenters` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nfvo_tenant_id` varchar(36) NOT NULL,
  `datacenter_id` varchar(36) NOT NULL,
  `datacenter_tenant_id` varchar(36) NOT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `datacenter_nfvo_tenant` (`datacenter_id`,`nfvo_tenant_id`),
  KEY `FK_nfvo_tenants_datacenters` (`datacenter_id`),
  KEY `FK_nfvo_tenants_vim_tenants` (`datacenter_tenant_id`),
  KEY `FK_tenants_datacenters_nfvo_tenants` (`nfvo_tenant_id`),
  CONSTRAINT `FK_tenants_datacenters_datacenter_tenants` FOREIGN KEY (`datacenter_tenant_id`) REFERENCES `datacenter_tenants` (`uuid`),
  CONSTRAINT `FK_tenants_datacenters_datacenters` FOREIGN KEY (`datacenter_id`) REFERENCES `datacenters` (`uuid`),
  CONSTRAINT `FK_tenants_datacenters_nfvo_tenants` FOREIGN KEY (`nfvo_tenant_id`) REFERENCES `nfvo_tenants` (`uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=86 DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='Scenarios defined by the user';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `uuids`
--

DROP TABLE IF EXISTS `uuids`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `uuids` (
  `uuid` varchar(36) NOT NULL,
  `root_uuid` varchar(36) DEFAULT NULL COMMENT 'Some related UUIDs can be grouped by this field, so that they can be deleted at once',
  `created_at` double NOT NULL,
  `used_at` varchar(36) DEFAULT NULL COMMENT 'Table that uses this UUID',
  PRIMARY KEY (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Table with all unique IDs used to avoid UUID repetitions among different elements';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vim_actions`
--

DROP TABLE IF EXISTS `vim_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vim_actions` (
  `instance_action_id` varchar(36) NOT NULL,
  `task_index` int(6) NOT NULL,
  `datacenter_vim_id` varchar(36) NOT NULL,
  `vim_id` varchar(64) DEFAULT NULL,
  `action` varchar(36) NOT NULL COMMENT 'CREATE,DELETE,START,STOP...',
  `item` enum('datacenters_flavors','datacenter_images','instance_nets','instance_vms','instance_interfaces') NOT NULL COMMENT 'table where the item is stored',
  `item_id` varchar(36) DEFAULT NULL COMMENT 'uuid of the entry in the table',
  `status` enum('SCHEDULED','BUILD','DONE','FAILED','SUPERSEDED') NOT NULL DEFAULT 'SCHEDULED',
  `extra` text COMMENT 'json with params:, depends_on: for the task',
  `error_msg` varchar(1024) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  PRIMARY KEY (`task_index`,`instance_action_id`),
  KEY `FK_actions_instance_actions` (`instance_action_id`),
  KEY `FK_actions_vims` (`datacenter_vim_id`),
  CONSTRAINT `FK_actions_instance_actions` FOREIGN KEY (`instance_action_id`) REFERENCES `instance_actions` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_actions_vims` FOREIGN KEY (`datacenter_vim_id`) REFERENCES `datacenter_tenants` (`uuid`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Table with the individual VIM actions.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vms`
--

DROP TABLE IF EXISTS `vms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vms` (
  `uuid` varchar(36) NOT NULL,
  `osm_id` varchar(255) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `vnf_id` varchar(36) NOT NULL,
  `count` smallint(6) NOT NULL DEFAULT '1',
  `flavor_id` varchar(36) NOT NULL COMMENT 'Link to flavor table',
  `image_id` varchar(36) NOT NULL COMMENT 'Link to image table',
  `image_path` varchar(100) DEFAULT NULL COMMENT 'Path where the image of the VM is located',
  `boot_data` text,
  `description` varchar(255) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `availability_zone` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `name_vnf_id` (`name`,`vnf_id`),
  KEY `FK_vms_vnfs` (`vnf_id`),
  KEY `FK_vms_images` (`image_id`),
  KEY `FK_vms_flavors` (`flavor_id`),
  CONSTRAINT `FK_vms_flavors` FOREIGN KEY (`flavor_id`) REFERENCES `flavors` (`uuid`),
  CONSTRAINT `FK_vms_images` FOREIGN KEY (`image_id`) REFERENCES `images` (`uuid`),
  CONSTRAINT `FK_vms_vnfs` FOREIGN KEY (`vnf_id`) REFERENCES `vnfs` (`uuid`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='VM definitions. It contains the set of VMs used by the VNF definitions.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vnfs`
--

DROP TABLE IF EXISTS `vnfs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vnfs` (
  `uuid` varchar(36) NOT NULL,
  `osm_id` varchar(255) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `short_name` varchar(255) DEFAULT NULL,
  `tenant_id` varchar(36) DEFAULT NULL,
  `physical` enum('true','false') NOT NULL DEFAULT 'false',
  `public` enum('true','false') NOT NULL DEFAULT 'false',
  `description` varchar(255) DEFAULT NULL,
  `vendor` varchar(255) DEFAULT NULL,
  `mgmt_access` varchar(2000) DEFAULT NULL,
  `created_at` double NOT NULL,
  `modified_at` double DEFAULT NULL,
  `class` varchar(36) DEFAULT 'MISC',
  `descriptor` text COMMENT 'Original text descriptor used for create the VNF',
  PRIMARY KEY (`uuid`),
  UNIQUE KEY `osm_id_tenant_id` (`osm_id`,`tenant_id`),
  KEY `FK_vnfs_nfvo_tenants` (`tenant_id`),
  CONSTRAINT `FK_vnfs_nfvo_tenants` FOREIGN KEY (`tenant_id`) REFERENCES `nfvo_tenants` (`uuid`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPACT COMMENT='VNF definitions. This is the catalogue of VNFs. It also includes Physical Network Functions or Physical Elements.\r\n';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database '{{mano_db}}'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-11-23 10:24:39





-- MySQL dump 10.13  Distrib 5.7.20, for Linux (x86_64)
--
-- Host: localhost    Database: {{mano_db}}
-- ------------------------------------------------------
-- Server version	5.7.20-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `schema_version`
--

LOCK TABLES `schema_version` WRITE;
/*!40000 ALTER TABLE `schema_version` DISABLE KEYS */;
INSERT INTO `schema_version` VALUES (1,'0.1','0.2.2','insert schema_version','2015-05-08'),(2,'0.2','0.2.5','new tables images,flavors','2015-07-13'),(3,'0.3','0.3.3','alter vim_tenant tables','2015-07-28'),(4,'0.4','0.3.5','enlarge graph field at sce_vnfs/nets','2015-10-20'),(5,'0.5','0.4.1','Add mac address for bridge interfaces','2015-12-14'),(6,'0.6','0.4.2','Adding VIM status info','2015-12-22'),(7,'0.7','0.4.3','Changing created_at time at database','2016-01-25'),(8,'0.8','0.4.32','Enlarging name at database','2016-02-01'),(9,'0.9','0.4.33','Add ACTIVE:NoMgmtIP to instance_vms table','2016-02-05'),(10,'0.10','0.4.36','tenant management of vnfs,scenarios','2016-03-08'),(11,'0.11','0.4.43','remove unique name at scenarios,instance_scenarios','2016-07-18'),(12,'0.12','0.4.46','create ip_profiles table, with foreign keys to all nets tables, and add ip_address column to interfaces and sce_interfaces','2016-08-29'),(13,'0.13','0.4.47','insert cloud-config at scenarios,instance_scenarios','2016-08-30'),(14,'0.14','0.4.57','remove unique index vim_net_id, instance_scenario_id','2016-09-26'),(15,'0.15','0.4.59','add columns universal_name and checksum at table images, add unique index universal_name_checksum, and change location to allow NULL; change column image_path in table vms to allow NULL','2016-09-27'),(16,'0.16','0.5.2','enlarge vim_tenant_name and id. New config at datacenter_tenants','2016-10-11'),(17,'0.17','0.5.3','Extra description json format of additional devices in datacenter_flavors','2016-12-20'),(18,'0.18','0.5.4','Add columns \'floating_ip\' and \'port_security\' at tables \'interfaces\' and \'instance_interfaces\'','2017-01-09'),(19,'0.19','0.5.5','Extra Boot-data content at VNFC (vms)','2017-01-11'),(20,'0.20','0.5.9','Added columns to store dataplane connectivity info','2017-03-13'),(21,'0.21','0.5.15','Edit instance_nets to allow instance_scenario_id=None and enlarge column dns_address at table ip_profiles','2017-06-02'),(22,'0.22','0.5.16','Changed type of ram in flavors from SMALLINT to MEDIUMINT','2017-06-02'),(23,'0.23','0.5.20','Changed type of ram in flavors from SMALLINT to MEDIUMINT','2017-08-29'),(24,'0.24','0.5.21','Added vnfd fields','2017-08-29'),(25,'0.25','0.5.22','Added osm_id to vnfs,scenarios','2017-09-01'),(26,'0.26','0.5.23','Several changes','2017-09-09'),(27,'0.27','0.5.25','Added encrypted_RO_priv_key,RO_pub_key to table nfvo_tenants','2017-09-29');
/*!40000 ALTER TABLE `schema_version` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-11-23 10:24:39
