from datetime import datetime
from uuid import uuid4

from mongoengine import DateTimeField, Document, UUIDField


class BaseDocument(Document):
    meta = {"abstract": True}
    id = UUIDField(default=uuid4, primary_key=True)
    created_at = DateTimeField(default=datetime.utcnow)
