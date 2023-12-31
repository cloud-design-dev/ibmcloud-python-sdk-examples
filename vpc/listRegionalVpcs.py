import argparse
import os

import ibm_vpc
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from rich import box
from rich.console import Console
from rich.table import Table

ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

authenticator = IAMAuthenticator(
    apikey=ibmcloud_api_key
)

def get_vpcs(region):
    service = ibm_vpc.VpcV1(authenticator=authenticator)
    service.set_service_url(f'https://{region}.iaas.cloud.ibm.com/v1')

    list_vpcs = service.list_vpcs().get_result()['vpcs']
    vpcs = []
    for vpc in list_vpcs:
        vpc_info = {'name': vpc['name'], 'id': vpc['id']}
        list_subnets = service.list_subnets().get_result()['subnets']
        subnets_in_vpc = [subnet for subnet in list_subnets if subnet['vpc']['id'] == vpc['id']]
        public_subnets = sum(1 for subnet in subnets_in_vpc if subnet.get('public_gateway'))
        private_subnets = len(subnets_in_vpc) - public_subnets
        vpc_info['subnets'] = f"[green]{public_subnets}[/green] / [white]{private_subnets}[/white]"

        list_instances = service.list_instances().get_result()['instances']
        instances_in_vpc = [instance for instance in list_instances if instance['vpc']['id'] == vpc['id']]
        total_instances = len(instances_in_vpc)
        running_instances = len([instance for instance in instances_in_vpc if instance['status'] == 'running'])
        stopped_instances = total_instances - running_instances
        vpc_info['instances'] = f"[yellow]{total_instances}[/yellow] / [green]{running_instances}[/green] / [red]{stopped_instances}[/red]"

        vpcs.append(vpc_info)

    return vpcs

def print_vpcs(vpcs):
    console = Console()

    table = Table(show_header=True, header_style="white", box=box.ROUNDED)  # Change header style to bold purple
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Subnets")
    table.add_column("Instances")

    for vpc in vpcs:
        table.add_row(vpc['name'], vpc['id'], vpc['subnets'], vpc['instances'])

    console.print(table)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List all VPCs in a region.')
    parser.add_argument('--region', type=str, required=True, help='The region to list VPCs from.')
    args = parser.parse_args()

    vpcs = get_vpcs(args.region)
    print_vpcs(vpcs)
