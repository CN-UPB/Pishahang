import time

from osm_ro import vimconn
from osm_ro.vimconn_kubernetes import vimconnector

import unittest
import mock

# vimconn =  vimconnector(uuid='123', name='kubernetes-vim', tenant_id='', tenant_name='', url='206.189.248.107', url_admin=None, user='user', passwd=None, log_level=None, config={}, persitent_info={})
# uid = vimconn.new_vminstance(name='nginx-pod', description=None, start=True, image_id='nginx:1.7.9', flavor_id=None, net_list=None, availability_zone_index='test-ns')[0]
# print uid
# print vimconn.get_vminstance(uid)['name']
# print vimconn.delete_vminstance(uid)



class TestSfcOperations(unittest.TestCase):
    def setUp(self):
        self.vimconn =  vimconnector(uuid='123', name='kubernetes-vim', tenant_id='', tenant_name='', url='206.189.248.107', url_admin=None, user='user', passwd=None, log_level=None, config={}, persitent_info={})

    def test_pod_workflow(self):
        # Create Pod
        uid = self.vimconn.new_vminstance(name='my-pod', description=None, start=True, image_id='nginx:1.7.9', flavor_id=None, net_list=None, availability_zone_index='default')[0]
        # Check if it got created
        self.assertEqual(self.vimconn.get_vminstance(uid)['name'], 'my-pod')
        # Delete Pod and wait for deletion
        self.vimconn.delete_vminstance(uid)
        time.sleep(5)
        # Check of it got deleted
        self.assertIsNone(self.vimconn.get_vminstance(uid))


if __name__ == '__main__':
    unittest.main()
