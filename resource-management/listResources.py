import os
import json
import logging
import csv
import click
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException
from ibm_platform_services.resource_controller_v2 import *
from ibm_platform_services import IamIdentityV1, ResourceManagerV2
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

@click.group()
def cli():
    """Group to hold our commands"""
    pass

ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

def setup_logging(default_path='../logging.json', default_level=logging.info, env_key='LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

def ibm_client():  
  authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
  iamIdentityService = IamIdentityV1(authenticator=authenticator)
  return iamIdentityService

def getAccountId():
    try:
        client = ibm_client()
        api_key = client.get_api_keys_details(
          iam_api_key=ibmcloud_api_key
        ).get_result()
    except ApiException as e:
        logging.error("API exception {}.".format(str(e)))
        quit(1)
    account_id = api_key["account_id"]
    return account_id

def resource_controller_service():
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    return ResourceControllerV2(authenticator=authenticator)

def resource_manager_service():
    authenticator = IAMAuthenticator(apikey=ibmcloud_api_key)
    return ResourceManagerV2(authenticator=authenticator)

def get_group_id_by_name(name):
    # rc_service = resource_controller_service()
    rm_service = resource_manager_service()
    account_id = getAccountId()
    resource_groups = rm_service.list_resource_groups(
        account_id=account_id,
    ).get_result()

    for group in resource_groups['resources']:
        if group['name'] == name:
            return group['id']
            
    return None

@cli.command()
@click.option('--resource-group', '-rg', help='Name of the Resource group to filter by', required=False)
def get_resources(resource_group):
    rg_id = None  # Default to None
    if resource_group:
        rg_id = get_group_id_by_name(resource_group)  # Function to fetch the resource group ID by name

    service = resource_controller_service()
    all_results = []
    pager = ResourceInstancesPager(
        client=service,
        resource_group_id=rg_id
    )
    while pager.has_next():
        next_page = pager.get_next()
        assert next_page is not None
        all_results.extend(next_page)

    # print(json.dumps(all_results, indent=2))

    resource_instances = []
    for result in all_results:
        resource_instances.append({
            'name' : result.get('name'),
            'state' : result.get('state'),
            'region' : result.get('region_id'),
            'created_at' : result.get('created_at'),
            'created_by' : result.get('created_by'),
            'resource_group_id' : result.get('resource_group_id'),
            'type': result.get('type'),
            'resource_id' : result.get('resource_id')
        })

    

    with open('resource_instances.csv', 'w', newline='') as csvfile:
        fieldnames = ['name', 'state', 'region', 'created_at', 'created_by', 'resource_group_id', 'type', 'resource_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resource_instances)
    
    return resource_instances

# for result in all_results:

#     print(f"name: {result.name}")

if __name__ == '__main__':
    cli()

