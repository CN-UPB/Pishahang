# -*- coding: utf-8 -*-

##
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
# This file is part of openmano
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##

'''
HTTP server implementing the openmano API. It will answer to POST, PUT, GET methods in the appropriate URLs
and will use the nfvo.py module to run the appropriate method.
Every YAML/JSON file is checked against a schema in openmano_schemas.py module.  
'''
__author__="Alfonso Tierno, Gerardo Garcia"
__date__ ="$17-sep-2014 09:07:15$"

import bottle
import yaml
import json
import threading
import time
import logging

from jsonschema import validate as js_v, exceptions as js_e
from openmano_schemas import vnfd_schema_v01, vnfd_schema_v02, \
                            nsd_schema_v01, nsd_schema_v02, nsd_schema_v03, scenario_edit_schema, \
                            scenario_action_schema, instance_scenario_action_schema, instance_scenario_create_schema_v01, \
                            tenant_schema, tenant_edit_schema,\
                            datacenter_schema, datacenter_edit_schema, datacenter_action_schema, datacenter_associate_schema,\
                            object_schema, netmap_new_schema, netmap_edit_schema, sdn_controller_schema, sdn_controller_edit_schema, \
                            sdn_port_mapping_schema, sdn_external_port_schema

import nfvo
import utils
from db_base import db_base_Exception
from functools import wraps

global mydb
global url_base
global logger
url_base="/openmano"
logger = None

HTTP_Bad_Request =          400
HTTP_Unauthorized =         401 
HTTP_Not_Found =            404 
HTTP_Forbidden =            403
HTTP_Method_Not_Allowed =   405 
HTTP_Not_Acceptable =       406
HTTP_Service_Unavailable =  503 
HTTP_Internal_Server_Error= 500 

def delete_nulls(var):
    if type(var) is dict:
        for k in var.keys():
            if var[k] is None: del var[k]
            elif type(var[k]) is dict or type(var[k]) is list or type(var[k]) is tuple: 
                if delete_nulls(var[k]): del var[k]
        if len(var) == 0: return True
    elif type(var) is list or type(var) is tuple:
        for k in var:
            if type(k) is dict: delete_nulls(k)
        if len(var) == 0: return True
    return False

def convert_datetime2str(var):
    '''Converts a datetime variable to a string with the format '%Y-%m-%dT%H:%i:%s'
    It enters recursively in the dict var finding this kind of variables
    '''
    if type(var) is dict:
        for k,v in var.items():
            if type(v) is float and k in ("created_at", "modified_at"):
                var[k] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(v) )
            elif type(v) is dict or type(v) is list or type(v) is tuple: 
                convert_datetime2str(v)
        if len(var) == 0: return True
    elif type(var) is list or type(var) is tuple:
        for v in var:
            convert_datetime2str(v)

def log_to_logger(fn):
    '''
    Wrap a Bottle request so that a log line is emitted after it's handled.
    (This decorator can be extended to take the desired logger as a param.)
    '''
    @wraps(fn)
    def _log_to_logger(*args, **kwargs):
        actual_response = fn(*args, **kwargs)
        # modify this to log exactly what you need:
        logger.info('FROM %s %s %s %s' % (bottle.request.remote_addr,
                                        bottle.request.method,
                                        bottle.request.url,
                                        bottle.response.status))
        return actual_response
    return _log_to_logger

class httpserver(threading.Thread):
    def __init__(self, db, admin=False, host='localhost', port=9090):
        #global url_base
        global mydb
        global logger
        #initialization
        if not logger:
            logger = logging.getLogger('openmano.http')
        threading.Thread.__init__(self)
        self.host = host
        self.port = port   #Port where the listen service must be started
        if admin==True:
            self.name = "http_admin"
        else:
            self.name = "http"
            #self.url_preffix = 'http://' + host + ':' + str(port) + url_base
            mydb = db
        #self.first_usable_connection_index = 10
        #self.next_connection_index = self.first_usable_connection_index #The next connection index to be used 
        #Ensure that when the main program exits the thread will also exit
        self.daemon = True
        self.setDaemon(True)
         
    def run(self):
        bottle.install(log_to_logger)
        bottle.run(host=self.host, port=self.port, debug=False, quiet=True)
           
def run_bottle(db, host_='localhost', port_=9090):
    '''used for launching in main thread, so that it can be debugged'''
    global mydb
    mydb = db
    bottle.run(host=host_, port=port_, debug=True) #quiet=True
    

@bottle.route(url_base + '/', method='GET')
def http_get():
    #print 
    return 'works' #TODO: to be completed

#
# Util functions
#

def change_keys_http2db(data, http_db, reverse=False):
    '''Change keys of dictionary data acording to the key_dict values
    This allow change from http interface names to database names.
    When reverse is True, the change is otherwise
    Attributes:
        data: can be a dictionary or a list
        http_db: is a dictionary with hhtp names as keys and database names as value
        reverse: by default change is done from http api to database. If True change is done otherwise
    Return: None, but data is modified'''
    if type(data) is tuple or type(data) is list:
        for d in data:
            change_keys_http2db(d, http_db, reverse)
    elif type(data) is dict or type(data) is bottle.FormsDict:
        if reverse:
            for k,v in http_db.items():
                if v in data: data[k]=data.pop(v)
        else:
            for k,v in http_db.items():
                if k in data: data[v]=data.pop(k)

def format_out(data):
    '''return string of dictionary data according to requested json, yaml, xml. By default json'''
    logger.debug("OUT: " + yaml.safe_dump(data, explicit_start=True, indent=4, default_flow_style=False, tags=False, encoding='utf-8', allow_unicode=True) )
    if 'application/yaml' in bottle.request.headers.get('Accept'):
        bottle.response.content_type='application/yaml'
        return yaml.safe_dump(data, explicit_start=True, indent=4, default_flow_style=False, tags=False, encoding='utf-8', allow_unicode=True) #, canonical=True, default_style='"'
    else: #by default json
        bottle.response.content_type='application/json'
        #return data #json no style
        return json.dumps(data, indent=4) + "\n"

def format_in(default_schema, version_fields=None, version_dict_schema=None, confidential_data=False):
    """
    Parse the content of HTTP request against a json_schema
    :param default_schema: The schema to be parsed by default if no version field is found in the client data. In None
        no validation is done
    :param version_fields: If provided it contains a tuple or list with the fields to iterate across the client data to
        obtain the version
    :param version_dict_schema: It contains a dictionary with the version as key, and json schema to apply as value.
        It can contain a None as key, and this is apply if the client data version does not match any key
    :return:  user_data, used_schema: if the data is successfully decoded and matches the schema.
        Launch a bottle abort if fails
    """
    #print "HEADERS :" + str(bottle.request.headers.items())
    try:
        error_text = "Invalid header format "
        format_type = bottle.request.headers.get('Content-Type', 'application/json')
        if 'application/json' in format_type:
            error_text = "Invalid json format "
            #Use the json decoder instead of bottle decoder because it informs about the location of error formats with a ValueError exception
            client_data = json.load(bottle.request.body)
            #client_data = bottle.request.json()
        elif 'application/yaml' in format_type:
            error_text = "Invalid yaml format "
            client_data = yaml.load(bottle.request.body)
        elif 'application/xml' in format_type:
            bottle.abort(501, "Content-Type: application/xml not supported yet.")
        else:
            logger.warning('Content-Type ' + str(format_type) + ' not supported.')
            bottle.abort(HTTP_Not_Acceptable, 'Content-Type ' + str(format_type) + ' not supported.')
            return
        # if client_data == None:
        #    bottle.abort(HTTP_Bad_Request, "Content error, empty")
        #    return
        if confidential_data:
            logger.debug('IN: %s', remove_clear_passwd (yaml.safe_dump(client_data, explicit_start=True, indent=4, default_flow_style=False,
                                              tags=False, encoding='utf-8', allow_unicode=True)))
        else:
            logger.debug('IN: %s', yaml.safe_dump(client_data, explicit_start=True, indent=4, default_flow_style=False,
                                              tags=False, encoding='utf-8', allow_unicode=True) )
        # look for the client provider version
        error_text = "Invalid content "
        if not default_schema and not version_fields:
            return client_data, None
        client_version = None
        used_schema = None
        if version_fields != None:
            client_version = client_data
            for field in version_fields:
                if field in client_version:
                    client_version = client_version[field]
                else:
                    client_version=None
                    break
        if client_version == None:
            used_schema = default_schema
        elif version_dict_schema != None:
            if client_version in version_dict_schema:
                used_schema = version_dict_schema[client_version]
            elif None in version_dict_schema:
                used_schema = version_dict_schema[None]
        if used_schema==None:
            bottle.abort(HTTP_Bad_Request, "Invalid schema version or missing version field")
            
        js_v(client_data, used_schema)
        return client_data, used_schema
    except (ValueError, yaml.YAMLError) as exc:
        error_text += str(exc)
        logger.error(error_text) 
        bottle.abort(HTTP_Bad_Request, error_text)
    except js_e.ValidationError as exc:
        logger.error("validate_in error, jsonschema exception at '%s' '%s' ", str(exc.path), str(exc.message))
        error_pos = ""
        if len(exc.path)>0: error_pos=" at " + ":".join(map(json.dumps, exc.path))
        bottle.abort(HTTP_Bad_Request, error_text + exc.message + error_pos)
    #except:
    #    bottle.abort(HTTP_Bad_Request, "Content error: Failed to parse Content-Type",  error_pos)
    #    raise

def filter_query_string(qs, http2db, allowed):
    '''Process query string (qs) checking that contains only valid tokens for avoiding SQL injection
    Attributes:
        'qs': bottle.FormsDict variable to be processed. None or empty is considered valid
        'http2db': dictionary with change from http API naming (dictionary key) to database naming(dictionary value)
        'allowed': list of allowed string tokens (API http naming). All the keys of 'qs' must be one of 'allowed'
    Return: A tuple with the (select,where,limit) to be use in a database query. All of then transformed to the database naming
        select: list of items to retrieve, filtered by query string 'field=token'. If no 'field' is present, allowed list is returned
        where: dictionary with key, value, taken from the query string token=value. Empty if nothing is provided
        limit: limit dictated by user with the query string 'limit'. 100 by default
    abort if not permited, using bottel.abort
    '''
    where={}
    limit=100
    select=[]
    #if type(qs) is not bottle.FormsDict:
    #    bottle.abort(HTTP_Internal_Server_Error, '!!!!!!!!!!!!!!invalid query string not a dictionary')
    #    #bottle.abort(HTTP_Internal_Server_Error, "call programmer")
    for k in qs:
        if k=='field':
            select += qs.getall(k)
            for v in select:
                if v not in allowed:
                    bottle.abort(HTTP_Bad_Request, "Invalid query string at 'field="+v+"'")
        elif k=='limit':
            try:
                limit=int(qs[k])
            except:
                bottle.abort(HTTP_Bad_Request, "Invalid query string at 'limit="+qs[k]+"'")
        else:
            if k not in allowed:
                bottle.abort(HTTP_Bad_Request, "Invalid query string at '"+k+"="+qs[k]+"'")
            if qs[k]!="null":  where[k]=qs[k]
            else: where[k]=None 
    if len(select)==0: select += allowed
    #change from http api to database naming
    for i in range(0,len(select)):
        k=select[i]
        if http2db and k in http2db: 
            select[i] = http2db[k]
    if http2db:
        change_keys_http2db(where, http2db)
    #print "filter_query_string", select,where,limit
    
    return select,where,limit

@bottle.hook('after_request')
def enable_cors():
    '''Don't know yet if really needed. Keep it just in case'''
    bottle.response.headers['Access-Control-Allow-Origin'] = '*'

@bottle.route(url_base + '/version', method='GET')
def http_get_version():
    return nfvo.get_version()
#
# VNFs
#

@bottle.route(url_base + '/tenants', method='GET')
def http_get_tenants():
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    select_,where_,limit_ = filter_query_string(bottle.request.query, None,
            ('uuid','name','description','created_at') )
    try:
        tenants = mydb.get_rows(FROM='nfvo_tenants', SELECT=select_,WHERE=where_,LIMIT=limit_)
        #change_keys_http2db(content, http2db_tenant, reverse=True)
        convert_datetime2str(tenants)
        data={'tenants' : tenants}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except db_base_Exception as e:
        logger.error("http_get_tenants error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/tenants/<tenant_id>', method='GET')
def http_get_tenant_id(tenant_id):
    '''get tenant details, can use both uuid or name'''
    #obtain data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        from_ = 'nfvo_tenants'
        select_, where_, limit_ = filter_query_string(bottle.request.query, None,
                                                      ('uuid', 'name', 'description', 'created_at'))
        what = 'uuid' if utils.check_valid_uuid(tenant_id) else 'name'
        where_[what] = tenant_id
        tenants = mydb.get_rows(FROM=from_, SELECT=select_,WHERE=where_)
        #change_keys_http2db(content, http2db_tenant, reverse=True)
        if len(tenants) == 0:
            bottle.abort(HTTP_Not_Found, "No tenant found with {}='{}'".format(what, tenant_id))
        elif len(tenants) > 1:
            bottle.abort(HTTP_Bad_Request, "More than one tenant found with {}='{}'".format(what, tenant_id))
        convert_datetime2str(tenants[0])
        data = {'tenant': tenants[0]}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except db_base_Exception as e:
        logger.error("http_get_tenant_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/tenants', method='POST')
def http_post_tenants():
    '''insert a tenant into the catalogue. '''
    #parse input data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content,_ = format_in( tenant_schema )
    r = utils.remove_extra_items(http_content, tenant_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try: 
        data = nfvo.new_tenant(mydb, http_content['tenant'])
        return http_get_tenant_id(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_tenants error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/tenants/<tenant_id>', method='PUT')
def http_edit_tenant_id(tenant_id):
    '''edit tenant details, can use both uuid or name'''
    #parse input data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content,_ = format_in( tenant_edit_schema )
    r = utils.remove_extra_items(http_content, tenant_edit_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    
    #obtain data, check that only one exist
    try: 
        tenant = mydb.get_table_by_uuid_name('nfvo_tenants', tenant_id)
        #edit data 
        tenant_id = tenant['uuid']
        where={'uuid': tenant['uuid']}
        mydb.update_rows('nfvo_tenants', http_content['tenant'], where)
        return http_get_tenant_id(tenant_id)
    except bottle.HTTPError:
        raise
    except db_base_Exception as e:
        logger.error("http_edit_tenant_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/tenants/<tenant_id>', method='DELETE')
def http_delete_tenant_id(tenant_id):
    '''delete a tenant from database, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        data = nfvo.delete_tenant(mydb, tenant_id)
        return format_out({"result":"tenant " + data + " deleted"})
    except bottle.HTTPError:
        raise
    except db_base_Exception as e:
        logger.error("http_delete_tenant_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/datacenters', method='GET')
def http_get_datacenters(tenant_id):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        if tenant_id != 'any':
            #check valid tenant_id
            nfvo.check_tenant(mydb, tenant_id)
        select_,where_,limit_ = filter_query_string(bottle.request.query, None,
                ('uuid','name','vim_url','type','created_at') )
        if tenant_id != 'any':
            where_['nfvo_tenant_id'] = tenant_id
            if 'created_at' in select_:
                select_[ select_.index('created_at') ] = 'd.created_at as created_at'
            if 'created_at' in where_:
                where_['d.created_at'] = where_.pop('created_at')
            datacenters = mydb.get_rows(FROM='datacenters as d join tenants_datacenters as td on d.uuid=td.datacenter_id',
                                          SELECT=select_,WHERE=where_,LIMIT=limit_)
        else:
            datacenters = mydb.get_rows(FROM='datacenters',
                                          SELECT=select_,WHERE=where_,LIMIT=limit_)
        #change_keys_http2db(content, http2db_tenant, reverse=True)
        convert_datetime2str(datacenters)
        data={'datacenters' : datacenters}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_datacenters error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>', method='GET')
def http_get_datacenter_id(tenant_id, datacenter_id):
    '''get datacenter details, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        if tenant_id != 'any':
            #check valid tenant_id
            nfvo.check_tenant(mydb, tenant_id)
        #obtain data
        what = 'uuid' if utils.check_valid_uuid(datacenter_id) else 'name'
        where_={}
        where_[what] = datacenter_id
        select_=['uuid', 'name','vim_url', 'vim_url_admin', 'type', 'd.config as config', 'description', 'd.created_at as created_at']
        if tenant_id != 'any':
            select_.append("datacenter_tenant_id")
            where_['td.nfvo_tenant_id']= tenant_id
            from_='datacenters as d join tenants_datacenters as td on d.uuid=td.datacenter_id'
        else:
            from_='datacenters as d'
        datacenters = mydb.get_rows(
                    SELECT=select_,
                    FROM=from_,
                    WHERE=where_)
    
        if len(datacenters)==0:
            bottle.abort( HTTP_Not_Found, "No datacenter found for tenant with {} '{}'".format(what, datacenter_id) )
        elif len(datacenters)>1: 
            bottle.abort( HTTP_Bad_Request, "More than one datacenter found for tenant with {} '{}'".format(what, datacenter_id) )
        datacenter = datacenters[0]
        if tenant_id != 'any':
            #get vim tenant info
            vim_tenants = mydb.get_rows(
                    SELECT=("vim_tenant_name", "vim_tenant_id", "user", "passwd", "config"),
                    FROM="datacenter_tenants",
                    WHERE={"uuid": datacenters[0]["datacenter_tenant_id"]},
                    ORDER_BY=("created", ) )
            del datacenter["datacenter_tenant_id"]
            datacenter["vim_tenants"] = vim_tenants
            for vim_tenant in vim_tenants:
                if vim_tenant["passwd"]:
                    vim_tenant["passwd"] = "******"
                if vim_tenant['config'] != None:
                    try:
                        config_dict = yaml.load(vim_tenant['config'])
                        vim_tenant['config'] = config_dict
                        if vim_tenant['config'].get('admin_password'):
                            vim_tenant['config']['admin_password'] = "******"
                        if vim_tenant['config'].get('vcenter_password'):
                            vim_tenant['config']['vcenter_password'] = "******"
                        if vim_tenant['config'].get('nsx_password'):
                            vim_tenant['config']['nsx_password'] = "******"
                    except Exception as e:
                        logger.error("Exception '%s' while trying to load config information", str(e))

        if datacenter['config'] != None:
            try:
                config_dict = yaml.load(datacenter['config'])
                datacenter['config'] = config_dict
                if datacenter['config'].get('admin_password'):
                    datacenter['config']['admin_password'] = "******"
                if datacenter['config'].get('vcenter_password'):
                    datacenter['config']['vcenter_password'] = "******"
                if datacenter['config'].get('nsx_password'):
                    datacenter['config']['nsx_password'] = "******"
            except Exception as e:
                logger.error("Exception '%s' while trying to load config information", str(e))
        #change_keys_http2db(content, http2db_datacenter, reverse=True)
        convert_datetime2str(datacenter)
        data={'datacenter' : datacenter}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/datacenters', method='POST')
def http_post_datacenters():
    '''insert a datacenter into the catalogue. '''
    #parse input data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content,_ = format_in(datacenter_schema, confidential_data=True)
    r = utils.remove_extra_items(http_content, datacenter_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        data = nfvo.new_datacenter(mydb, http_content['datacenter'])
        return http_get_datacenter_id('any', data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_datacenters error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/datacenters/<datacenter_id_name>', method='PUT')
def http_edit_datacenter_id(datacenter_id_name):
    '''edit datacenter details, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #parse input data
    http_content,_ = format_in( datacenter_edit_schema )
    r = utils.remove_extra_items(http_content, datacenter_edit_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    
    try:
        datacenter_id = nfvo.edit_datacenter(mydb, datacenter_id_name, http_content['datacenter'])
        return http_get_datacenter_id('any', datacenter_id)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_edit_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/sdn_controllers', method='POST')
def http_post_sdn_controller(tenant_id):
    '''insert a sdn controller into the catalogue. '''
    #parse input data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content,_ = format_in( sdn_controller_schema )
    try:
        logger.debug("tenant_id: "+tenant_id)
        #logger.debug("content: {}".format(http_content['sdn_controller']))

        data = nfvo.sdn_controller_create(mydb, tenant_id, http_content['sdn_controller'])
        return format_out({"sdn_controller": nfvo.sdn_controller_list(mydb, tenant_id, data)})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_sdn_controller error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/sdn_controllers/<controller_id>', method='PUT')
def http_put_sdn_controller_update(tenant_id, controller_id):
    '''Update sdn controller'''
    #parse input data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content,_ = format_in( sdn_controller_edit_schema )
#    r = utils.remove_extra_items(http_content, datacenter_schema)
#    if r:
#        logger.debug("Remove received extra items %s", str(r))
    try:
        #logger.debug("tenant_id: "+tenant_id)
        logger.debug("content: {}".format(http_content['sdn_controller']))

        data = nfvo.sdn_controller_update(mydb, tenant_id, controller_id, http_content['sdn_controller'])
        return format_out({"sdn_controller": nfvo.sdn_controller_list(mydb, tenant_id, controller_id)})

    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_sdn_controller error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/sdn_controllers', method='GET')
def http_get_sdn_controller(tenant_id):
    '''get sdn controllers list, can use both uuid or name'''
    try:
        logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)

        data = {'sdn_controllers': nfvo.sdn_controller_list(mydb, tenant_id)}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_sdn_controller error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/sdn_controllers/<controller_id>', method='GET')
def http_get_sdn_controller_id(tenant_id, controller_id):
    '''get sdn controller details, can use both uuid or name'''
    try:
        logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
        data = nfvo.sdn_controller_list(mydb, tenant_id, controller_id)
        return format_out({"sdn_controllers": data})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_sdn_controller_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/sdn_controllers/<controller_id>', method='DELETE')
def http_delete_sdn_controller_id(tenant_id, controller_id):
    '''delete sdn controller, can use both uuid or name'''
    try:
        logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
        data = nfvo.sdn_controller_delete(mydb, tenant_id, controller_id)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delete_sdn_controller_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/sdn_mapping', method='POST')
def http_post_datacenter_sdn_port_mapping(tenant_id, datacenter_id):
    '''Set the sdn port mapping for a datacenter. '''
    #parse input data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content, _ = format_in(sdn_port_mapping_schema)
#    r = utils.remove_extra_items(http_content, datacenter_schema)
#    if r:
#        logger.debug("Remove received extra items %s", str(r))
    try:
        data = nfvo.datacenter_sdn_port_mapping_set(mydb, tenant_id, datacenter_id, http_content['sdn_port_mapping'])
        return format_out({"sdn_port_mapping": data})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_datacenter_sdn_port_mapping error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/sdn_mapping', method='GET')
def http_get_datacenter_sdn_port_mapping(tenant_id, datacenter_id):
    '''get datacenter sdn mapping details, can use both uuid or name'''
    try:
        logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)

        data = nfvo.datacenter_sdn_port_mapping_list(mydb, tenant_id, datacenter_id)
        return format_out({"sdn_port_mapping": data})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_datacenter_sdn_port_mapping error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/sdn_mapping', method='DELETE')
def http_delete_datacenter_sdn_port_mapping(tenant_id, datacenter_id):
    '''clean datacenter sdn mapping, can use both uuid or name'''
    try:
        logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
        data = nfvo.datacenter_sdn_port_mapping_delete(mydb, tenant_id, datacenter_id)
        return format_out({"result": data})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delete_datacenter_sdn_port_mapping error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/networks', method='GET')  #deprecated
@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/netmaps', method='GET')
@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/netmaps/<netmap_id>', method='GET')
def http_getnetmap_datacenter_id(tenant_id, datacenter_id, netmap_id=None):
    '''get datacenter networks, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #obtain data
    try:
        datacenter_dict = mydb.get_table_by_uuid_name('datacenters', datacenter_id, "datacenter") 
        where_= {"datacenter_id":datacenter_dict['uuid']}
        if netmap_id:
            if utils.check_valid_uuid(netmap_id):
                where_["uuid"] = netmap_id
            else:
                where_["name"] = netmap_id
        netmaps =mydb.get_rows(FROM='datacenter_nets',
                                        SELECT=('name','vim_net_id as vim_id', 'uuid', 'type','multipoint','shared','description', 'created_at'),
                                        WHERE=where_ ) 
        convert_datetime2str(netmaps)
        utils.convert_str2boolean(netmaps, ('shared', 'multipoint') )
        if netmap_id and len(netmaps)==1:
            data={'netmap' : netmaps[0]}
        elif netmap_id and len(netmaps)==0:
            bottle.abort(HTTP_Not_Found, "No netmap found with " + " and ".join(map(lambda x: str(x[0])+": "+str(x[1]), where_.iteritems())) )
            return 
        else:
            data={'netmaps' : netmaps}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_getnetwork_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/netmaps', method='DELETE')
@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/netmaps/<netmap_id>', method='DELETE')
def http_delnetmap_datacenter_id(tenant_id, datacenter_id, netmap_id=None):
    '''get datacenter networks, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #obtain data
    try:
        datacenter_dict = mydb.get_table_by_uuid_name('datacenters', datacenter_id, "datacenter") 
        where_= {"datacenter_id":datacenter_dict['uuid']}
        if netmap_id:
            if utils.check_valid_uuid(netmap_id):
                where_["uuid"] = netmap_id
            else:
                where_["name"] = netmap_id
        #change_keys_http2db(content, http2db_tenant, reverse=True)
        deleted = mydb.delete_row(FROM='datacenter_nets', WHERE= where_) 
        if deleted == 0 and netmap_id:
            bottle.abort(HTTP_Not_Found, "No netmap found with " + " and ".join(map(lambda x: str(x[0])+": "+str(x[1]), where_.iteritems())) )
        if netmap_id:
            return format_out({"result": "netmap %s deleted" % netmap_id})
        else:
            return format_out({"result": "%d netmap deleted" % deleted})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delnetmap_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/netmaps/upload', method='POST')
def http_uploadnetmap_datacenter_id(tenant_id, datacenter_id):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        netmaps = nfvo.datacenter_new_netmap(mydb, tenant_id, datacenter_id, None)
        convert_datetime2str(netmaps)
        utils.convert_str2boolean(netmaps, ('shared', 'multipoint') )
        data={'netmaps' : netmaps}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_uploadnetmap_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/netmaps', method='POST')
def http_postnetmap_datacenter_id(tenant_id, datacenter_id):
    '''creates a new netmap'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #parse input data
    http_content,_ = format_in( netmap_new_schema )
    r = utils.remove_extra_items(http_content, netmap_new_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        #obtain data, check that only one exist
        netmaps = nfvo.datacenter_new_netmap(mydb, tenant_id, datacenter_id, http_content)
        convert_datetime2str(netmaps)
        utils.convert_str2boolean(netmaps, ('shared', 'multipoint') )
        data={'netmaps' : netmaps}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_postnetmap_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/netmaps/<netmap_id>', method='PUT')
def http_putnettmap_datacenter_id(tenant_id, datacenter_id, netmap_id):
    '''edit a  netmap'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #parse input data
    http_content,_ = format_in( netmap_edit_schema )
    r = utils.remove_extra_items(http_content, netmap_edit_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    
    #obtain data, check that only one exist
    try:
        nfvo.datacenter_edit_netmap(mydb, tenant_id, datacenter_id, netmap_id, http_content)
        return http_getnetmap_datacenter_id(tenant_id, datacenter_id, netmap_id)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_putnettmap_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))
    

@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>/action', method='POST')
def http_action_datacenter_id(tenant_id, datacenter_id):
    '''perform an action over datacenter, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #parse input data
    http_content,_ = format_in( datacenter_action_schema )
    r = utils.remove_extra_items(http_content, datacenter_action_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        #obtain data, check that only one exist
        result = nfvo.datacenter_action(mydb, tenant_id, datacenter_id, http_content)
        if 'net-update' in http_content:
            return http_getnetmap_datacenter_id(datacenter_id)
        else:
            return format_out(result)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_action_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/datacenters/<datacenter_id>', method='DELETE')
def http_delete_datacenter_id( datacenter_id):
    '''delete a tenant from database, can use both uuid or name'''
    
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        data = nfvo.delete_datacenter(mydb, datacenter_id)
        return format_out({"result":"datacenter '" + data + "' deleted"})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delete_datacenter_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>', method='POST')
def http_associate_datacenters(tenant_id, datacenter_id):
    '''associate an existing datacenter to a this tenant. '''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #parse input data
    http_content,_ = format_in(datacenter_associate_schema, confidential_data=True)
    r = utils.remove_extra_items(http_content, datacenter_associate_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        id_ = nfvo.associate_datacenter_to_tenant(mydb, tenant_id, datacenter_id, 
                                    http_content['datacenter'].get('vim_tenant'),
                                    http_content['datacenter'].get('vim_tenant_name'),
                                    http_content['datacenter'].get('vim_username'),
                                    http_content['datacenter'].get('vim_password'),
                                    http_content['datacenter'].get('config')
        )
        return http_get_datacenter_id(tenant_id, id_)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_associate_datacenters error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>', method='PUT')
def http_associate_datacenters_edit(tenant_id, datacenter_id):
    '''associate an existing datacenter to a this tenant. '''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #parse input data
    http_content,_ = format_in( datacenter_associate_schema )
    r = utils.remove_extra_items(http_content, datacenter_associate_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        id_ = nfvo.edit_datacenter_to_tenant(mydb, tenant_id, datacenter_id,
                                    http_content['datacenter'].get('vim_tenant'),
                                    http_content['datacenter'].get('vim_tenant_name'),
                                    http_content['datacenter'].get('vim_username'),
                                    http_content['datacenter'].get('vim_password'),
                                    http_content['datacenter'].get('config')
        )
        return http_get_datacenter_id(tenant_id, id_)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_associate_datacenters_edit error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/datacenters/<datacenter_id>', method='DELETE')
def http_deassociate_datacenters(tenant_id, datacenter_id):
    '''deassociate an existing datacenter to a this tenant. '''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        data = nfvo.deassociate_datacenter_to_tenant(mydb, tenant_id, datacenter_id)
        return format_out({"result": data})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_deassociate_datacenters error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/vim/<datacenter_id>/network/<network_id>/attach', method='POST')
def http_post_vim_net_sdn_attach(tenant_id, datacenter_id, network_id):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content, _ = format_in(sdn_external_port_schema)
    try:
        data = nfvo.vim_net_sdn_attach(mydb, tenant_id, datacenter_id, network_id, http_content)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_vim_net_sdn_attach error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/vim/<datacenter_id>/network/<network_id>/detach', method='DELETE')
@bottle.route(url_base + '/<tenant_id>/vim/<datacenter_id>/network/<network_id>/detach/<port_id>', method='DELETE')
def http_delete_vim_net_sdn_detach(tenant_id, datacenter_id, network_id, port_id=None):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        data = nfvo.vim_net_sdn_detach(mydb, tenant_id, datacenter_id, network_id, port_id)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delete_vim_net_sdn_detach error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))
       
@bottle.route(url_base + '/<tenant_id>/vim/<datacenter_id>/<item>', method='GET')
@bottle.route(url_base + '/<tenant_id>/vim/<datacenter_id>/<item>/<name>', method='GET')
def http_get_vim_items(tenant_id, datacenter_id, item, name=None):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        data = nfvo.vim_action_get(mydb, tenant_id, datacenter_id, item, name)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_vim_items error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/vim/<datacenter_id>/<item>/<name>', method='DELETE')
def http_del_vim_items(tenant_id, datacenter_id, item, name):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        data = nfvo.vim_action_delete(mydb, tenant_id, datacenter_id, item, name)
        return format_out({"result":data})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_del_vim_items error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/vim/<datacenter_id>/<item>', method='POST')
def http_post_vim_items(tenant_id, datacenter_id, item):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content,_ = format_in( object_schema )
    try:
        data = nfvo.vim_action_create(mydb, tenant_id, datacenter_id, item, http_content)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_vim_items error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/vnfs', method='GET')
def http_get_vnfs(tenant_id):
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        if tenant_id != 'any':
            #check valid tenant_id
            nfvo.check_tenant(mydb, tenant_id)
        select_,where_,limit_ = filter_query_string(bottle.request.query, None,
                ('uuid', 'name', 'osm_id', 'description', 'public', "tenant_id", "created_at") )
        if tenant_id != "any":
            where_["OR"]={"tenant_id": tenant_id, "public": True}
        vnfs = mydb.get_rows(FROM='vnfs', SELECT=select_, WHERE=where_, LIMIT=limit_)
        # change_keys_http2db(content, http2db_vnf, reverse=True)
        utils.convert_str2boolean(vnfs, ('public',))
        convert_datetime2str(vnfs)
        data={'vnfs': vnfs}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_vnfs error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/vnfs/<vnf_id>', method='GET')
def http_get_vnf_id(tenant_id,vnf_id):
    '''get vnf details, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        vnf = nfvo.get_vnf_id(mydb,tenant_id,vnf_id)
        utils.convert_str2boolean(vnf, ('public',))
        convert_datetime2str(vnf)
        return format_out(vnf)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_vnf_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/vnfs', method='POST')
def http_post_vnfs(tenant_id):
    """ Insert a vnf into the catalogue. Creates the flavor and images, and fill the tables at database
    :param tenant_id: tenant that this vnf belongs to
    :return:
    """
    # print "Parsing the YAML file of the VNF"
    # parse input data
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content, used_schema = format_in( vnfd_schema_v01, ("schema_version",), {"0.2": vnfd_schema_v02})
    r = utils.remove_extra_items(http_content, used_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        if used_schema == vnfd_schema_v01:
            vnf_id = nfvo.new_vnf(mydb,tenant_id,http_content)
        elif used_schema == vnfd_schema_v02:
            vnf_id = nfvo.new_vnf_v02(mydb,tenant_id,http_content)
        else:
            logger.warning('Unexpected schema_version: %s', http_content.get("schema_version"))
            bottle.abort(HTTP_Bad_Request, "Invalid schema version")
        return http_get_vnf_id(tenant_id, vnf_id)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_vnfs error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/v3/<tenant_id>/vnfd', method='POST')
def http_post_vnfs_v3(tenant_id):
    """
    Insert one or several VNFs in the catalog, following OSM IM
    :param tenant_id: tenant owner of the VNF
    :return: The detailed list of inserted VNFs, following the old format
    """
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content, _ = format_in(None)
    try:
        vnfd_uuid_list = nfvo.new_vnfd_v3(mydb, tenant_id, http_content)
        vnfd_list = []
        for vnfd_uuid in vnfd_uuid_list:
            vnf = nfvo.get_vnf_id(mydb, tenant_id, vnfd_uuid)
            utils.convert_str2boolean(vnf, ('public',))
            convert_datetime2str(vnf)
            vnfd_list.append(vnf["vnf"])
        return format_out({"vnfd": vnfd_list})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_vnfs error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/vnfs/<vnf_id>', method='DELETE')
def http_delete_vnf_id(tenant_id, vnf_id):
    '''delete a vnf from database, and images and flavors in VIM when appropriate, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #check valid tenant_id and deletes the vnf, including images, 
    try:
        data = nfvo.delete_vnf(mydb,tenant_id,vnf_id)
        #print json.dumps(data, indent=4)
        return format_out({"result":"VNF " + data + " deleted"})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delete_vnf_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


#@bottle.route(url_base + '/<tenant_id>/hosts/topology', method='GET')
#@bottle.route(url_base + '/<tenant_id>/physicalview/Madrid-Alcantara', method='GET')
@bottle.route(url_base + '/<tenant_id>/physicalview/<datacenter>', method='GET')
def http_get_hosts(tenant_id, datacenter):
    '''get the tidvim host hopology from the vim.'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    #print "http_get_hosts received by tenant " + tenant_id + ' datacenter ' + datacenter
    try:
        if datacenter == 'treeview':
            data = nfvo.get_hosts(mydb, tenant_id)
        else:
            #openmano-gui is using a hardcoded value for the datacenter
            result, data = nfvo.get_hosts_info(mydb, tenant_id) #, datacenter)
        
        if result < 0:
            #print "http_get_hosts error %d %s" % (-result, data)
            bottle.abort(-result, data)
        else:
            convert_datetime2str(data)
            #print json.dumps(data, indent=4)
            return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_hosts error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<path:path>', method='OPTIONS')
def http_options_deploy(path):
    '''For some reason GUI web ask for OPTIONS that must be responded'''
    #TODO: check correct path, and correct headers request
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    bottle.response.set_header('Access-Control-Allow-Methods','POST, GET, PUT, DELETE, OPTIONS')
    bottle.response.set_header('Accept','application/yaml,application/json')
    bottle.response.set_header('Content-Type','application/yaml,application/json')
    bottle.response.set_header('Access-Control-Allow-Headers','content-type')
    bottle.response.set_header('Access-Control-Allow-Origin','*')
    return

@bottle.route(url_base + '/<tenant_id>/topology/deploy', method='POST')
def http_post_deploy(tenant_id):
    '''post topology deploy.'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)

    http_content, used_schema = format_in( nsd_schema_v01, ("schema_version",), {2: nsd_schema_v02})
    #r = utils.remove_extra_items(http_content, used_schema)
    #if r is not None: print "http_post_deploy: Warning: remove extra items ", r
    #print "http_post_deploy input: ",  http_content
    
    try:
        scenario_id = nfvo.new_scenario(mydb, tenant_id, http_content)
        instance = nfvo.start_scenario(mydb, tenant_id, scenario_id, http_content['name'], http_content['name'])
        #print json.dumps(data, indent=4)
        return format_out(instance)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_deploy error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/topology/verify', method='POST')
def http_post_verify(tenant_id):
    #TODO:
#    '''post topology verify'''
#    print "http_post_verify by tenant " + tenant_id + ' datacenter ' + datacenter
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    return 

#
# SCENARIOS
#

@bottle.route(url_base + '/<tenant_id>/scenarios', method='POST')
def http_post_scenarios(tenant_id):
    '''add a scenario into the catalogue. Creates the scenario and its internal structure in the OPENMANO DB'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content, used_schema = format_in( nsd_schema_v01, ("schema_version",), {2: nsd_schema_v02, "0.3": nsd_schema_v03})
    #r = utils.remove_extra_items(http_content, used_schema)
    #if r is not None: print "http_post_scenarios: Warning: remove extra items ", r
    #print "http_post_scenarios input: ",  http_content
    try:
        if used_schema == nsd_schema_v01:
            scenario_id = nfvo.new_scenario(mydb, tenant_id, http_content)
        elif used_schema == nsd_schema_v02:
            scenario_id = nfvo.new_scenario_v02(mydb, tenant_id, http_content, "0.2")
        elif used_schema == nsd_schema_v03:
            scenario_id = nfvo.new_scenario_v02(mydb, tenant_id, http_content, "0.3")
        else:
            logger.warning('Unexpected schema_version: %s', http_content.get("schema_version"))
            bottle.abort(HTTP_Bad_Request, "Invalid schema version")
        #print json.dumps(data, indent=4)
        #return format_out(data)
        return http_get_scenario_id(tenant_id, scenario_id)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_scenarios error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/v3/<tenant_id>/nsd', method='POST')
def http_post_nsds_v3(tenant_id):
    """
    Insert one or several NSDs in the catalog, following OSM IM
    :param tenant_id: tenant owner of the NSD
    :return: The detailed list of inserted NSDs, following the old format
    """
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content, _ = format_in(None)
    try:
        nsd_uuid_list = nfvo.new_nsd_v3(mydb, tenant_id, http_content)
        nsd_list = []
        for nsd_uuid in nsd_uuid_list:
            scenario = mydb.get_scenario(nsd_uuid, tenant_id)
            convert_datetime2str(scenario)
            nsd_list.append(scenario)
        data = {'nsd': nsd_list}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_nsds_v3 error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/scenarios/<scenario_id>/action', method='POST')
def http_post_scenario_action(tenant_id, scenario_id):
    '''take an action over a scenario'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    # parse input data
    http_content, _ = format_in(scenario_action_schema)
    r = utils.remove_extra_items(http_content, scenario_action_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        # check valid tenant_id
        nfvo.check_tenant(mydb, tenant_id)
        if "start" in http_content:
            data = nfvo.start_scenario(mydb, tenant_id, scenario_id, http_content['start']['instance_name'], \
                        http_content['start'].get('description',http_content['start']['instance_name']),
                        http_content['start'].get('datacenter') )
            return format_out(data)
        elif "deploy" in http_content:   #Equivalent to start
            data = nfvo.start_scenario(mydb, tenant_id, scenario_id, http_content['deploy']['instance_name'],
                        http_content['deploy'].get('description',http_content['deploy']['instance_name']),
                        http_content['deploy'].get('datacenter') )
            return format_out(data)
        elif "reserve" in http_content:   #Reserve resources
            data = nfvo.start_scenario(mydb, tenant_id, scenario_id, http_content['reserve']['instance_name'],
                        http_content['reserve'].get('description',http_content['reserve']['instance_name']),
                        http_content['reserve'].get('datacenter'),  startvms=False )
            return format_out(data)
        elif "verify" in http_content:   #Equivalent to start and then delete
            data = nfvo.start_scenario(mydb, tenant_id, scenario_id, http_content['verify']['instance_name'],
                        http_content['verify'].get('description',http_content['verify']['instance_name']),
                        http_content['verify'].get('datacenter'), startvms=False )
            instance_id = data['uuid']
            nfvo.delete_instance(mydb, tenant_id,instance_id)
            return format_out({"result":"Verify OK"})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_scenario_action error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/scenarios', method='GET')
def http_get_scenarios(tenant_id):
    '''get scenarios list'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id) 
        #obtain data
        s,w,l=filter_query_string(bottle.request.query, None,
                                  ('uuid', 'name', 'osm_id', 'description', 'tenant_id', 'created_at', 'public'))
        if tenant_id != "any":
            w["OR"] = {"tenant_id": tenant_id, "public": True}
        scenarios = mydb.get_rows(SELECT=s, WHERE=w, LIMIT=l, FROM='scenarios')
        convert_datetime2str(scenarios)
        utils.convert_str2boolean(scenarios, ('public',) )
        data={'scenarios':scenarios}
        #print json.dumps(scenarios, indent=4)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_scenarios error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/scenarios/<scenario_id>', method='GET')
def http_get_scenario_id(tenant_id, scenario_id):
    '''get scenario details, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id) 
        #obtain data
        scenario = mydb.get_scenario(scenario_id, tenant_id)
        convert_datetime2str(scenario)
        data={'scenario' : scenario}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_scenarios error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/scenarios/<scenario_id>', method='DELETE')
def http_delete_scenario_id(tenant_id, scenario_id):
    '''delete a scenario from database, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id)
        #obtain data
        data = mydb.delete_scenario(scenario_id, tenant_id)
        #print json.dumps(data, indent=4)
        return format_out({"result":"scenario " + data + " deleted"})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delete_scenario_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/scenarios/<scenario_id>', method='PUT')
def http_put_scenario_id(tenant_id, scenario_id):
    '''edit an existing scenario id'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    http_content,_ = format_in( scenario_edit_schema )
    #r = utils.remove_extra_items(http_content, scenario_edit_schema)
    #if r is not None: print "http_put_scenario_id: Warning: remove extra items ", r
    #print "http_put_scenario_id input: ",  http_content
    try:
        nfvo.edit_scenario(mydb, tenant_id, scenario_id, http_content)
        #print json.dumps(data, indent=4)
        #return format_out(data)
        return http_get_scenario_id(tenant_id, scenario_id)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_put_scenario_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

@bottle.route(url_base + '/<tenant_id>/instances', method='POST')
def http_post_instances(tenant_id):
    '''create an instance-scenario'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    # parse input data
    http_content, used_schema = format_in(instance_scenario_create_schema_v01)
    r = utils.remove_extra_items(http_content, used_schema)
    if r is not None:
        logger.warning("http_post_instances: Warning: remove extra items %s", str(r))
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id) 
        data = nfvo.create_instance(mydb, tenant_id, http_content["instance"])
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_instances error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

#
# INSTANCES
#
@bottle.route(url_base + '/<tenant_id>/instances', method='GET')
def http_get_instances(tenant_id):
    '''get instance list'''
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id) 
        #obtain data
        s,w,l=filter_query_string(bottle.request.query, None, ('uuid', 'name', 'scenario_id', 'tenant_id', 'description', 'created_at'))
        if tenant_id != "any":
            w['tenant_id'] = tenant_id
        instances = mydb.get_rows(SELECT=s, WHERE=w, LIMIT=l, FROM='instance_scenarios')
        convert_datetime2str(instances)
        utils.convert_str2boolean(instances, ('public',) )
        data={'instances':instances}
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_instances error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/instances/<instance_id>', method='GET')
def http_get_instance_id(tenant_id, instance_id):
    '''get instances details, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id) 
        if tenant_id == "any":
            tenant_id = None
        #obtain data (first time is only to check that the instance exists)
        instance_dict = mydb.get_instance_scenario(instance_id, tenant_id, verbose=True)
        try:
            nfvo.refresh_instance(mydb, tenant_id, instance_dict)
        except (nfvo.NfvoException, db_base_Exception) as e:
            logger.warn("nfvo.refresh_instance couldn't refresh the status of the instance: %s" % str(e))
        # obtain data with results upated
        instance = mydb.get_instance_scenario(instance_id, tenant_id)
        # Workaround to SO, convert vnfs:vms:interfaces:ip_address from ";" separated list to report the first value
        for vnf in instance.get("vnfs", ()):
            for vm in vnf.get("vms", ()):
                for iface in vm.get("interfaces", ()):
                    if iface.get("ip_address"):
                        index = iface["ip_address"].find(";")
                        if index >= 0:
                            iface["ip_address"] = iface["ip_address"][:index]
        convert_datetime2str(instance)
        # print json.dumps(instance, indent=4)
        return format_out(instance)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_instance_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/instances/<instance_id>', method='DELETE')
def http_delete_instance_id(tenant_id, instance_id):
    '''delete instance from VIM and from database, can use both uuid or name'''
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id) 
        if tenant_id == "any":
            tenant_id = None
        #obtain data
        message = nfvo.delete_instance(mydb, tenant_id,instance_id)
        return format_out({"result":message})
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_delete_instance_id error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/instances/<instance_id>/action', method='POST')
def http_post_instance_scenario_action(tenant_id, instance_id):
    """
    take an action over a scenario instance
    :param tenant_id: tenant where user belongs to
    :param instance_id: instance indentity
    :return:
    """
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    # parse input data
    http_content, _ = format_in(instance_scenario_action_schema)
    r = utils.remove_extra_items(http_content, instance_scenario_action_schema)
    if r:
        logger.debug("Remove received extra items %s", str(r))
    try:
        #check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id) 

        #print "http_post_instance_scenario_action input: ", http_content
        #obtain data
        instance = mydb.get_instance_scenario(instance_id, tenant_id)
        instance_id = instance["uuid"]
        
        data = nfvo.instance_action(mydb, tenant_id, instance_id, http_content)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_post_instance_scenario_action error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))


@bottle.route(url_base + '/<tenant_id>/instances/<instance_id>/action', method='GET')
@bottle.route(url_base + '/<tenant_id>/instances/<instance_id>/action/<action_id>', method='GET')
def http_get_instance_scenario_action(tenant_id, instance_id, action_id=None):
    """
    List the actions done over an instance, or the action details
    :param tenant_id: tenant where user belongs to. Can be "any" to ignore
    :param instance_id: instance id, can be "any" to get actions of all instances
    :return:
    """
    logger.debug('FROM %s %s %s', bottle.request.remote_addr, bottle.request.method, bottle.request.url)
    try:
        # check valid tenant_id
        if tenant_id != "any":
            nfvo.check_tenant(mydb, tenant_id)
        data = nfvo.instance_action_get(mydb, tenant_id, instance_id, action_id)
        return format_out(data)
    except bottle.HTTPError:
        raise
    except (nfvo.NfvoException, db_base_Exception) as e:
        logger.error("http_get_instance_scenario_action error {}: {}".format(e.http_code, str(e)))
        bottle.abort(e.http_code, str(e))
    except Exception as e:
        logger.error("Unexpected exception: ", exc_info=True)
        bottle.abort(HTTP_Internal_Server_Error, type(e).__name__ + ": " + str(e))

def remove_clear_passwd(data):
    """
    Removes clear passwords from the data received
    :param data: data with clear password
    :return: data without the password information
    """

    passw = ['password: ', 'passwd: ']

    for pattern in passw:
        init = data.find(pattern)
        while init != -1:
            end = data.find('\n', init)
            data = data[:init] + '{}******'.format(pattern) + data[end:]
            init += 1
            init = data.find(pattern, init)
    return data

@bottle.error(400)
@bottle.error(401) 
@bottle.error(404) 
@bottle.error(403)
@bottle.error(405) 
@bottle.error(406)
@bottle.error(409)
@bottle.error(503) 
@bottle.error(500)
def error400(error):
    e={"error":{"code":error.status_code, "type":error.status, "description":error.body}}
    bottle.response.headers['Access-Control-Allow-Origin'] = '*'
    return format_out(e)

