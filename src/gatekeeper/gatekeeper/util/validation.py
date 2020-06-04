"""
Helper functions related to the validation of json schemas
"""

from pathlib import Path

import jsonschema
import yaml
from gatekeeper.models.descriptors import DescriptorType

SPEC_DIR = Path(__file__).parent / "../../specification"

DESCRIPTOR_SPEC_DIR = SPEC_DIR / "schemas/descriptors"

schemaMap = {}

for descriptorType, filename in [
    (DescriptorType.SERVICE, "service.yml"),
    (DescriptorType.OPENSTACK, "openstack.yml"),
    (DescriptorType.KUBERNETES, "kubernetes.yml"),
]:
    with (DESCRIPTOR_SPEC_DIR / filename).open() as schema:
        schemaMap[descriptorType.value] = yaml.safe_load(schema)


def validateDescriptor(type: str, descriptor: dict):
    if type == DescriptorType.AWS.value:
        # No schema for AWS descriptors yet
        return

    return jsonschema.validate(descriptor, schemaMap[type])
