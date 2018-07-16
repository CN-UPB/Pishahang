#!/usr/bin/python3

# 
#   Copyright 2016 RIFT.IO Inc
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


import sys
import rw_peas
from gi import require_version
require_version('RwCal', '1.0')

from gi.repository import RwcalYang
from gi.repository.RwTypes import RwStatus
import argparse
import logging
import rwlogger

persistent_resources = {
    'vms'      : [],
    'networks' : [],
}


RIFT_IMAGE_AMI = 'ami-7070231a'

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger('rift.cal.awsresources')
logger.setLevel(logging.INFO)

def get_cal_plugin():
    """
        Load AWS cal plugin
    """
    plugin = rw_peas.PeasPlugin('rwcal_aws', 'RwCal-1.0')
    engine, info, extension = plugin()
    cal = plugin.get_interface("Cloud")
    rwloggerctx = rwlogger.RwLog.Ctx.new("Cal-Log")
    try:
        rc = cal.init(rwloggerctx)
        assert rc == RwStatus.SUCCESS
    except Exception as e:
        logger.error("ERROR:Cal plugin instantiation failed with exception %s", repr(e))
    else:
        logger.info("AWS Cal plugin successfully instantiated")
        return cal

def get_cal_account(**kwargs):
    """
    Returns AWS cal account
    """
    account                        = RwcalYang.YangData_RwProject_Project_CloudAccounts_CloudAccountList()
    account.account_type           = "aws"
    account.aws.key = kwargs['key']
    account.aws.secret = kwargs['secret']
    account.aws.region = kwargs['region']
    if 'ssh_key' in kwargs and kwargs['ssh_key'] is not None:
        account.aws.ssh_key = kwargs['ssh_key']
    account.aws.availability_zone = kwargs['availability_zone']
    if 'vpcid' in kwargs and kwargs['vpcid'] is not None: 
        account.aws.vpcid =  kwargs['vpcid']
    if 'default_subnet_id' in kwargs and kwargs['default_subnet_id'] is not None:
        account.aws.default_subnet_id = kwargs['default_subnet_id']
    return account

class AWSResources(object):
    """
    Class with methods to manage AWS resources
    """
    def __init__(self, **kwargs):
        self._cal      = get_cal_plugin()
        self._acct     = get_cal_account(**kwargs)

    def get_image_list(self):
        """
        Get Image list 
        """
        logger.info("Initiating Get image list")
        rc, rsp = self._cal.get_image_list(self._acct)

        print("Return resp: rsp ", rsp)

        logger.info("Get image list complete")


    def get_image(self, image_ami_id):
        """
        Get Image from AMI id
        """
        logger.info("Initiating Get image")
        rc, rsp = self._cal.get_image(self._acct, image_ami_id)

        print("Return code: rc ", rc)
        print("Return resp: rsp ", rsp)

        logger.info("Get image complete")



def main():
    """
    Main routine

    New AWS credentials were created as follows:
    User: aws_riftio
    Access Key ID: AKIAJQ4D3X5WO3P6JXKA
    Secret Access key: 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
    Pasword: RhN*q2ze*fpY

    The following AWS cloud account config can be used on LP CLI:
       cloud account AWS account-type aws aws key AKIAJQ4D3X5WO3P6JXKA secret 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 region us-east-1 vpcid vpc-cb1cd2af ssh-key rift-awskey availability-zone us-east-1c default-subnet-id subnet-73796d04 plugin-name rwcal_aws dynamic-flavor-support true`
    """
    parser = argparse.ArgumentParser(description='Script to manage AWS resources')

    parser.add_argument('--aws-key',
                        action = 'store',
                        dest = 'aws_key',
                        type = str,
                        help='AWS key')

    parser.add_argument('--aws-secret',
                        action = 'store',
                        dest = 'aws_secret',
                        type = str,
                        help='AWS secret')

    parser.add_argument('--aws-region',
                        action = 'store',
                        dest = 'aws_region',
                        type = str,
                        help='AWS region')

    parser.add_argument('--aws-az',
                        action = 'store',
                        dest = 'aws_az',
                        type = str,
                        help='AWS Availability zone')

    parser.add_argument('--aws-sshkey',
                        action = 'store',
                        dest = 'aws_sshkey',
                        type = str,
                        help='AWS SSH Key to login to instance')

    parser.add_argument('--aws-vpcid',
                        action = 'store',
                        dest = 'aws_vpcid',
                        type = str,
                        help='AWS VPC ID to use to indicate non default VPC')

    parser.add_argument('--aws-default-subnet',
                        action = 'store',
                        dest = 'aws_default_subnet',
                        type = str,
                        help='AWS Default subnet id in VPC to be used for mgmt network')

    argument = parser.parse_args()

    '''
    User: aws_riftio
    Access Key ID: AKIAJQ4D3X5WO3P6JXKA
    Secret Access key: 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
    Pasword: RhN*q2ze*fpY

    cloud account AWS account-type aws aws key AKIAJQ4D3X5WO3P6JXKA secret 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 region us-east-1 vpcid vpc-cb1cd2af ssh-key rift-awskey availability-zone us-east-1c default-subnet-id subnet-73796d04 plugin-name rwcal_aws dynamic-flavor-support true
    '''

    argument.aws_key = "AKIAJQ4D3X5WO3P6JXKA"
    argument.aws_secret = "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"
    argument.aws_region = "us-east-1"
    argument.aws_az = "us-east-1c"
    argument.aws_sshkey = "rift-awskey"
    argument.aws_vpcid = "vpc-cb1cd2af"
    argument.aws_default_subnet = "subnet-73796d04"

    if (argument.aws_key is None or argument.aws_secret is None or argument.aws_region is None or
       argument.aws_az is None):
        logger.error("Missing mandatory params. AWS Key, Secret, Region, AZ and SSH key are mandatory params")
        sys.exit(-1)


    ### Start processing
    logger.info("Instantiating cloud-abstraction-layer")
    drv = AWSResources(key=argument.aws_key, secret=argument.aws_secret, region=argument.aws_region, availability_zone = argument.aws_az, 
                       ssh_key = argument.aws_sshkey, vpcid = argument.aws_vpcid, default_subnet_id = argument.aws_default_subnet)
    logger.info("Instantiating cloud-abstraction-layer.......[Done]")

    logger.info("Testing image list APIs")
    drv.get_image_list()
    logger.info("Finished testing image list APIs")

    logger.info("Testing get image APIs for rift ping image - Present in Owner account")
    drv.get_image('ami-eb0a5f81')
    logger.info("Finished testing get image APIs")

    logger.info("Testing get image APIs for public vyos image")
    drv.get_image('ami-9ea315f6')
    logger.info("Finished testing get image APIs")

    logger.info("Testing get image APIs for public PalotAlto FW image")
    drv.get_image('ami-34ca984f')
    logger.info("Finished testing get image APIs")


if __name__ == '__main__':
    main()
