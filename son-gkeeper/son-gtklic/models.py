
from app import db
import uuid
import datetime

class License(db.Model):
    valid_status = ["ACTIVE", "INACTIVE"]
    license_types = ["PUBLIC", "PRIVATE"]

    service_uuid = db.Column(db.String, nullable=False)
    user_uuid = db.Column(db.String, nullable=False)
    license_uuid = db.Column(db.String, primary_key=True, default=str(uuid.uuid4()))

    license_type = db.Column(db.String, nullable=False, default="PUBLIC")
    description = db.Column(db.String)
    validation_url = db.Column(db.String)
    status = db.Column(db.String, nullable=False, default="ACTIVE")

    def __init__(self, service_uuid, user_uuid, description, validation_url=None, status="ACTIVE", license_type="PUBLIC"):
        self.license_uuid = str(uuid.uuid4())
        self.service_uuid = service_uuid
        self.user_uuid = user_uuid
        self.description = description
        self.validation_url = validation_url
        self.license_type = license_type
        self.status = status

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'license_uuid': self.license_uuid,
            'user_uuid': self.user_uuid,
            'service_uuid': self.service_uuid,

            'license_type': self.license_type,
            'description': self.description,
            'validation_url': self.validation_url,
            'status': self.status
        }
