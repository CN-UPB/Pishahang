from typing import List
from uuid import UUID, uuid4

from appcfg import get_config
from bson import ObjectId
from eve import Eve
from eve.io.base import BaseJSONEncoder
from eve.io.mongo import Validator
from jsonschema import ValidationError, validate

from repository.resources import resources

config = get_config(__name__)


class JsonEncoder(BaseJSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, ObjectId):
            return str(obj)
        else:
            return super(JsonEncoder, self).default(obj)


class JsonSchemaValidator(Validator):
    """
    A Validator subclass that adds JSON schema validation for items according to a
    `jsonschema` domain property
    """

    def validate(self, document, schema=None, update=False, normalize=True):

        super(JsonSchemaValidator, self).validate(
            document, schema=schema, update=update, normalize=normalize
        )

        resource_config = app.config["DOMAIN"][self.resource]
        if "jsonschema" in resource_config:
            try:
                validate(instance=document, schema=resource_config["jsonschema"])
            except ValidationError as e:
                self._error(".".join(e.path) if len(e.path) > 0 else ".", e.message)

        return len(self._errors) == 0

    def _validate_type_uuid(self, value):
        try:
            return str(UUID(value))
        except ValueError:
            pass


def make_domain_config(resources: dict):
    """
    Given a dict that maps resource names to JSON schemas, creates a configuration dict
    for the Eve `DOMAIN` setting.
    """
    return {
        name: {
            "jsonschema": schema,
            "allow_unknown": True,
            "schema": {"id": {"type": "uuid"}},
        }
        for name, schema in resources.items()
    }


settings = {
    "MONGO_URI": config["mongo_uri"],
    "RENDERERS": ["eve.render.JSONRenderer"],
    "HATEOAS": False,
    "IF_MATCH": False,
    "RESOURCE_METHODS": ["GET", "POST"],
    "ITEM_METHODS": ["GET", "PATCH", "PUT", "DELETE"],
    "LAST_UPDATED": "updated_at",
    "DATE_CREATED": "created_at",
    "ITEM_URL": 'regex("[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}")',
    "DOMAIN": make_domain_config(resources),
    "ALLOW_UNKNOWN": False,
}

app = Eve(settings=settings, json_encoder=JsonEncoder, validator=JsonSchemaValidator)
app.name = "repository"


def generate_id(resource_name, items):
    # Generate uuids for inserted items
    for item in items:
        item["_id"] = str(uuid4()) if "id" not in item else item["id"]


app.on_insert += generate_id


def map_id(resource, item: dict):
    if "_id" in item:
        item["id"] = item.pop("_id")


app.on_fetched_item += map_id


def map_ids(resource, response: List[dict]):
    for item in response["_items"]:
        map_id(resource, item)


app.on_fetched_resource += map_ids
