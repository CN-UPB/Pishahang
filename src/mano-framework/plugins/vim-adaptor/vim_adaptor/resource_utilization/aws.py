import vim_adaptor.models.vims as vims
from vim_adaptor.exceptions import VimConnectionError

import boto3


def get_resource_utilization(vim: vims.AwsVim):
    try:
        boto3.client(
            "ec2",
            aws_access_key_id=vim.access_key,
            aws_secret_access_key=vim.secret_key,
            region_name="eu-central-1",  # The region doesn't really matter here, but it is required
        ).describe_account_attributes()
        return {}
    except Exception as e:
        raise VimConnectionError(str(e))
