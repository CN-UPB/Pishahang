"""
Functions to validate data against Pishahang JSON schemas
"""

import json
from pathlib import Path

import jsonschema

from gatekeeper.models.descriptors import DescriptorType

DESCRIPTOR_SCHEMA_DIR = Path(__file__).parents[3] / "schemas/bundled/descriptors"

schemaMap = {}

for descriptorType, filename in [
    (DescriptorType.SERVICE, "service/service"),
    (DescriptorType.OPENSTACK, "functions/openstack"),
    (DescriptorType.KUBERNETES, "functions/kubernetes"),
    (DescriptorType.AWS, "functions/aws"),
]:
    with (DESCRIPTOR_SCHEMA_DIR / filename).with_suffix(".json").open() as schema:
        schemaMap[descriptorType.value] = json.load(schema)


def validateDescriptor(type: str, descriptor: dict):
    return jsonschema.validate(descriptor, schemaMap[type])
