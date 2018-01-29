import os
import json
import unittest
import xmlrunner
import uuid
import subprocess
import time
from datetime import datetime
from app import app, db

app.config.from_pyfile('settings.py')
if app.config['PORT'] == '5000':
    validation_url = "http://localhost:5001"
else:
    validation_url = "http://localhost:5000"

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        # Uncomment and change to use a different database for testing
        #app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://user:password@db_ip:5432/db_name"
        self.app = app.test_client()
        db.create_all()
        FNULL = open(os.devnull, 'w')
        self.p =  subprocess.Popen(['python','test_resources/validate.py'],stdout=FNULL, stderr=subprocess.STDOUT)
        time.sleep(0.5)

    def tearDown(self):
        db.session.remove()
        self.p.terminate()
        self.p.wait()
        db.drop_all()

    def test_add_private_license(self):
        # Test adding a license
        service_uuid = str(uuid.uuid4())
        user_uuid = str(uuid.uuid4())

        # Adding active License
        response = self.app.post("/api/v1/licenses/", data=json.dumps(dict(
                                                        service_uuid=service_uuid,
                                                        user_uuid=user_uuid,
                                                        description="Test",
                                                        license_type="private",
                                                        validation_url=validation_url,
                                                        status="active")),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        resp_json = json.loads(response.data)

        license_uuid = resp_json["data"]["license_uuid"]
        desc = resp_json["data"]["description"]
        status = resp_json["data"]["status"]
        license_type = resp_json["data"]["license_type"]

        self.assertEqual(desc, "Test")
        self.assertEqual(status, "ACTIVE")
        self.assertEqual(license_type, "PRIVATE")

    def test_add_same_license(self):

        # Test adding a license
        service_uuid = str(uuid.uuid4())
        user_uuid = str(uuid.uuid4())

        # Adding active License
        response = self.app.post("/api/v1/licenses/", data=json.dumps(dict(
                                                        service_uuid=service_uuid,
                                                        user_uuid=user_uuid,
                                                        description="Test",
                                                        license_type="private",
                                                        validation_url=validation_url,
                                                        status="active")),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 201)

        # Testing adding a license that the same user already has for a service of that type
        response = self.app.post("/api/v1/licenses/", data=json.dumps(dict(
                                                        service_uuid=service_uuid,
                                                        user_uuid=user_uuid,
                                                        description="Test",
                                                        license_type="private",
                                                        validation_url=validation_url,
                                                        status="active")),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 409)


    def test_add_public_license(self):

        # Adding active public License

        service_uuid = str(uuid.uuid4())
        user_uuid = str(uuid.uuid4())

        response = self.app.post("/api/v1/licenses/", data=json.dumps(dict(
                                                        service_uuid=service_uuid,
                                                        user_uuid=user_uuid,
                                                        description="Test",
                                                        license_type="public",
                                                        status="active")),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        resp_json = json.loads(response.data)

        status = resp_json["data"]["status"]
        license_type = resp_json["data"]["license_type"]

        self.assertEqual(status, "ACTIVE")
        self.assertEqual(license_type, "PUBLIC")

    def test_get_license(self):
        # Test getting a license

        service_uuid = str(uuid.uuid4())
        user_uuid = str(uuid.uuid4())
        startingDate = datetime.now()

        # Adding active License
        response = self.app.post("/api/v1/licenses/", data=json.dumps(dict(
                                                      service_uuid=service_uuid,
                                                      user_uuid=user_uuid,
                                                      description="Test",
                                                      license_type="private",
                                                      validation_url=validation_url,
                                                      status="active")),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        resp_json = json.loads(response.data)
        license_uuid = str(resp_json["data"]["license_uuid"])
        # Test get all licenses
        response = self.app.get("/api/v1/licenses/")
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)

        license_list = []
        for i in resp_json["data"]["licenses"]:
            license_list.append(i["license_uuid"])

        self.assertTrue(license_uuid in license_list)
        # Test get a specific license if is valid
        response = self.app.get("/api/v1/licenses/%s/" %license_uuid)
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)

        self.assertEqual(license_uuid, resp_json["data"]["license_uuid"])

        # Test if a license is valid
        response = self.app.head("/api/v1/licenses/%s/"%license_uuid)
        self.assertEqual(response.status_code, 200)

    def test_cancel_license(self):
        # Test canceling a license

        service_uuid = str(uuid.uuid4())
        user_uuid = str(uuid.uuid4())
        # Adding active License
        response = self.app.post("/api/v1/licenses/", data=json.dumps(dict(
                                                        service_uuid=service_uuid,
                                                        user_uuid=user_uuid,
                                                        description="Test",
                                                        license_type="private",
                                                        validation_url=validation_url,
                                                        status="active")),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        resp_json = json.loads(response.data)
        license_uuid = resp_json["data"]["license_uuid"]

        # Cancel a license
        response = self.app.delete("/api/v1/licenses/%s/"%license_uuid)
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)
        self.assertEqual(license_uuid, resp_json["data"]["license_uuid"])
        self.assertEqual(resp_json["data"]["status"], "INACTIVE")

if __name__ == '__main__':
#    FNULL = open(os.devnull, 'w')
#    p = subprocess.Popen(['python','test_resources/validate.py'], stdout=FNULL, stderr=subprocess.STDOUT)
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
#    p.terminate()
#    p.wait()
