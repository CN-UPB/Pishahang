
#
#   Copyright 2016-2017 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import json
import logging
import os
import yaml

import gi
gi.require_version('RwNsdYang', '1.0')
gi.require_version('RwProjectNsdYang', '1.0')
gi.require_version('RwVnfdYang', '1.0')
gi.require_version('RwProjectVnfdYang', '1.0')
gi.require_version('RwYang', '1.0')
from gi.repository import (
        RwNsdYang,
        RwVnfdYang,
        NsdYang,
        VnfdYang,
        RwProjectNsdYang,
        RwProjectVnfdYang,
        ProjectNsdYang,
        ProjectVnfdYang,
        RwYang,
        )

from rift.mano.utils.project import NS_PROJECT
from rift.rwlib.translation.json2xml import InvalidSchemaException

class UnknownExtensionError(Exception):
    pass


class SerializationError(Exception):
    pass


def decode(desc_data):
    if isinstance(desc_data, bytes):
        desc_data = desc_data.decode()

    return desc_data


class ProtoMessageSerializer(object):
    """(De)Serializer/deserializer fo a specific protobuf message into various formats"""
    libyang_model = None

    def __init__(self, yang_ns, yang_pb_cls,
                 yang_ns_project, yang_pb_project_cls):
        """ Create a serializer for a specific protobuf message """
        self._yang_ns = yang_ns
        self._yang_pb_cls = yang_pb_cls
        self._yang_ns_project = yang_ns_project
        self._yang_pb_project_cls = yang_pb_project_cls

        self._log = logging.getLogger('rw-maon-log')

    @classmethod
    def _deserialize_extension_method_map(cls):
        return {
                ".xml": cls._from_xml_file_hdl,
                ".yml": cls._from_yaml_file_hdl,
                ".yaml": cls._from_yaml_file_hdl,
                ".json": cls._from_json_file_hdl,
                }

    @classmethod
    def _serialize_extension_method_map(cls):
        return {
                ".xml": cls.to_xml_string,
                ".yml": cls.to_yaml_string,
                ".yaml": cls.to_yaml_string,
                ".json": cls.to_json_string,
                }

    @classmethod
    def is_supported_file(cls, filename):
        """Returns whether a file has a supported file extension

        Arguments:
            filename - A descriptor file

        Returns:
            True if file extension is supported, False otherwise

        """
        _, extension = os.path.splitext(filename)
        extension_lc = extension.lower()

        return extension_lc in cls._deserialize_extension_method_map()

    @property
    def yang_namespace(self):
        """ The Protobuf's GI namespace class (e.g. RwVnfdYang) """
        return self._yang_ns

    @property
    def yang_class(self):
        """ The Protobuf's GI class (e.g. RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd) """
        return self._yang_pb_cls

    @property
    def yang_ns_project(self):
        """ The Protobuf's GI namespace class (e.g. RwProjectVnfdYang) """
        return self._yang_ns_project

    @property
    def yang_class_project(self):
        """ The Protobuf's GI class (e.g. RwProjectVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd) """
        return self._yang_pb_project_cls

    @property
    def model(self):
        cls = self.__class__

        # Cache the libyang model for the serializer class
        if cls.libyang_model is None:
            cls.libyang_model = RwYang.model_create_libyang()
            cls.libyang_model.load_schema_ypbc(self.yang_namespace.get_schema())
            cls.libyang_model.load_schema_ypbc(self.yang_ns_project.get_schema())

        return cls.libyang_model

    def _from_xml_file_hdl(self, file_hdl, project=None):
        xml = file_hdl.read()

        return self.yang_class.from_xml_v2(self.model, decode(xml), strict=False) \
            if not project else self._yang_pb_project_cls.from_xml_v2(self.model, decode(xml), strict=False)

    def _from_json_file_hdl(self, file_hdl, project=None):
        jstr = file_hdl.read()
        self._log.debug("Convert from json file: {}".format(jstr))

        try:
            if not project:
                desc_msg = self.yang_class.from_json(self.model, decode(jstr), strict=False)
            else:
                desc_msg = self._yang_pb_project_cls.from_json(self.model, decode(jstr), strict=False)

            self._log.debug("desc_msg: {}".format(desc_msg.as_dict()))
            return self.yang_class_project.from_dict(desc_msg.as_dict())
        except Exception as e:
            self._log.exception(e)
            raise e

    def _from_yaml_file_hdl(self, file_hdl, project=None):
        yml = file_hdl.read()

        try:
            desc_msg = self.yang_class.from_yaml(self.model, decode(yml), strict=True)
        except InvalidSchemaException as invalid_scheme_exception:
            self._log.error("Exception raised during schema translation, %s. Launchpad will" \
                            "continue to process the remaining elements ", str(invalid_scheme_exception))
            desc_msg = self.yang_class.from_yaml(self.model, decode(yml), strict=False)
        except Exception as e:
            self._log.exception(e)
            raise e

        return self.yang_class_project.from_dict(desc_msg.as_dict()) 

    def to_desc_msg(self, pb_msg, project_rooted=True):
        """Convert to and from project rooted pb msg  descriptor to catalog
           rooted pb msg
           project_rooted: if pb_msg is project rooted or not
        """
        if project_rooted:
            if isinstance(pb_msg, self._yang_pb_project_cls):
                return self._yang_pb_cls.from_dict(pb_msg.as_dict())
            elif isinstance(pb_msg, self._yang_pb_cls):
                return pb_msg

        else:
            if isinstance(pb_msg, self._yang_pb_cls):
                return self._yang_pb_project_cls.from_dict(pb_msg.as_dict())
            elif isinstance(pb_msg, self._yang_pb_project_cls):
                return pb_msg

        raise TypeError("Invalid protobuf message type provided: {}".format(type(pb_msg)))


    def to_json_string(self, pb_msg, project_ns=False):
        """ Serialize a protobuf message into JSON

        Arguments:
            pb_msg - A GI-protobuf object of type provided into constructor
            project_ns - Need the desc in project namespace, required for
                         posting to Restconf as part of onboarding

        Returns:
            A JSON string representing the protobuf message

        Raises:
            SerializationError - Message could not be serialized
            TypeError - Incorrect protobuf type provided
        """
        self._log.debug("Convert desc to json (ns:{}): {}".format(project_ns, pb_msg.as_dict()))
        try:
            # json_str = pb_msg.to_json(self.model)

            desc_msg = self.to_desc_msg(pb_msg, not project_ns)
            json_str = desc_msg.to_json(self.model)
            if project_ns:
                # Remove rw-project:project top level element
                dic = json.loads(json_str)
                jstr = json.dumps(dic[NS_PROJECT][0])
            else:
                jstr = json_str

        except Exception as e:
            raise SerializationError(e)

        self._log.debug("Convert desc to json: {}".format(jstr))
        return jstr

    def to_yaml_string(self, pb_msg, project_ns=False):
        """ Serialize a protobuf message into YAML

        Arguments:
            pb_msg - A GI-protobuf object of type provided into constructor
            project_ns - Need the desc in project namespace, required for
                         posting to Restconf as part of onboarding

        Returns:
            A YAML string representing the protobuf message

        Raises:
            SerializationError - Message could not be serialized
            TypeError - Incorrect protobuf type provided
        """
        self._log.debug("Convert desc to yaml (ns:{}): {}".format(project_ns, pb_msg.as_dict()))
        try:
            desc_msg = self.to_desc_msg(pb_msg, not project_ns)
            yaml_str = desc_msg.to_yaml(self.model)
            if project_ns:
                # Remove rw-project:project top level element
                dic = yaml.loads(yaml_str)
                ystr = yaml.dump(dic[NS_PROJECT][0])
            else:
                ystr = yaml_str


        except Exception as e:
            self._log.exception("Exception converting to yaml: {}".format(e))
            raise SerializationError(e)

        return ystr

    def to_xml_string(self, pb_msg):
        """ Serialize a protobuf message into XML

        Arguments:
            pb_msg - A GI-protobuf object of type provided into constructor

        Returns:
            A XML string representing the protobuf message

        Raises:
            SerializationError - Message could not be serialized
            TypeError - Incorrect protobuf type provided
        """
        try:
            desc_msg = self.to_desc_msg(pb_msg)
            xml_str = desc_msg.to_xml_v2(self.model)

        except Exception as e:
            self._log.exception("Exception converting to xml: {}".format(e))
            raise SerializationError(e)

        return xml_str

    def from_file_hdl(self, file_hdl, extension, project=None):
        """ Returns the deserialized protobuf message from file contents

        This function determines the serialization format based on file extension

        Arguments:
            file_hdl - The file hdl to deserialize (set at pos 0)
            extension - Extension of the file format (second item of os.path.splitext())

        Returns:
            A GI-Proto message of type that was provided into the constructor

        Raises:
            UnknownExtensionError - File extension is not of a known serialization format
            SerializationError - File failed to be deserialized into the protobuf message
        """

        extension_lc = extension.lower()
        extension_map = self._deserialize_extension_method_map()

        if extension_lc not in extension_map:
            raise UnknownExtensionError("Cannot detect message format for %s extension" % extension_lc)

        try:
            self._log.debug("Converting from json..project = {}".format(project))
            msg = extension_map[extension_lc](self, file_hdl, project)
        except Exception as e:
            raise SerializationError(e)

        return msg

    def to_string(self, pb_msg, extension):
        """ Returns the serialized protobuf message for a particular file extension

        This function determines the serialization format based on file extension

        Arguments:
            pb_msg - A GI-protobuf object of type provided into constructor
            extension - Extension of the file format (second item of os.path.splitext())

        Returns:
            A GI-Proto message of type that was provided into the constructor

        Raises:
            UnknownExtensionError - File extension is not of a known serialization format
            SerializationError - File failed to be deserialized into the protobuf message
        """

        extension_lc = extension.lower()
        extension_map = self._serialize_extension_method_map()

        if extension_lc not in extension_map:
            raise UnknownExtensionError("Cannot detect message format for %s extension" % extension_lc)

        try:
            msg = extension_map[extension_lc](self, pb_msg)
        except Exception as e:
            raise SerializationError(e)

        return msg


class VnfdSerializer(ProtoMessageSerializer):
    """ Creates a serializer for the VNFD descriptor"""
    def __init__(self):
        super().__init__(VnfdYang, VnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd,
                         ProjectVnfdYang, ProjectVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd)


class NsdSerializer(ProtoMessageSerializer):
    """ Creates a serializer for the NSD descriptor"""
    def __init__(self):
        super().__init__(NsdYang, NsdYang.YangData_Nsd_NsdCatalog_Nsd,
                         ProjectNsdYang, ProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd)


class RwVnfdSerializer(ProtoMessageSerializer):
    """ Creates a serializer for the VNFD descriptor"""
    def __init__(self):
        super().__init__(RwVnfdYang, RwVnfdYang.YangData_Vnfd_VnfdCatalog_Vnfd,
                         RwProjectVnfdYang, RwProjectVnfdYang.YangData_RwProject_Project_VnfdCatalog_Vnfd)


class RwNsdSerializer(ProtoMessageSerializer):
    """ Creates a serializer for the NSD descriptor"""
    def __init__(self):
        super().__init__(RwNsdYang, RwNsdYang.YangData_Nsd_NsdCatalog_Nsd,
                         RwProjectNsdYang, RwProjectNsdYang.YangData_RwProject_Project_NsdCatalog_Nsd)
