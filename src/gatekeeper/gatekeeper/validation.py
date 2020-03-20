"""
Helper functions related to the validation of json schemas
"""

import os

import jsonschema
import yaml

SPEC_DIR = os.path.join(os.path.dirname(__file__), '../specification/')

with open(SPEC_DIR + "/schemas/csd.yml") as schema:
    csdSchema = yaml.safe_load(schema)

with open(SPEC_DIR + "/schemas/vnfd.yml") as schema:
    vnfdSchema = yaml.safe_load(schema)


def validateServiceDescriptor(descriptor: dict):
    return jsonschema.validate(descriptor, csdSchema)


def validateFunctionDescriptor(descriptor: dict):
    return jsonschema.validate(descriptor, vnfdSchema)
