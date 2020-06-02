"""
Helper functions related to the validation of json schemas
"""

from pathlib import Path

import jsonschema
import yaml

SPEC_DIR = Path(__file__).parent / "../../specification"

with (SPEC_DIR / "/schemas/csd.yml").open as schema:
    csdSchema = yaml.safe_load(schema)

with (SPEC_DIR / "/schemas/vnfd.yml").open as schema:
    vnfdSchema = yaml.safe_load(schema)


def validateServiceDescriptor(descriptor: dict):
    return jsonschema.validate(descriptor, csdSchema)


def validateFunctionDescriptor(descriptor: dict):
    return jsonschema.validate(descriptor, vnfdSchema)
