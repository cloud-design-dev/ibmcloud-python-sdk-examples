#!/usr/bin/env python3
# Author: Ryan Tiffany
# Copyright (c) 2023
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = 'ryantiffany'
import os
from haikunator import Haikunator
import json
import click
from ibm_code_engine_sdk.code_engine_v2 import *
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

ibmcloud_api_key = os.environ.get('IBMCLOUD_API_KEY')
if not ibmcloud_api_key:
    raise ValueError("IBMCLOUD_API_KEY environment variable not found")

# code_engine_project = os.environ.get('CODE_ENGINE_PROJECT')
# if not code_engine_project:
#     raise ValueError("CODE_ENGINE_PROJECT environment variable not found")

code_engine_region = os.environ.get('CODE_ENGINE_REGION')
if not code_engine_region:
    raise ValueError("CODE_ENGINE_REGION environment variable not found")

haikunator = Haikunator()
prefix = haikunator.haikunate(token_length=0, delimiter='')


def ceClient():
    authenticator = IAMAuthenticator(
        apikey=ibmcloud_api_key
    )

    code_engine_service = CodeEngineV2(authenticator=authenticator)
    code_engine_service.set_service_url('https://api.'+code_engine_region+'.codeengine.cloud.ibm.com/v2')
    return code_engine_service

def get_project_id(project_name):
    code_engine_service = ceClient()
    status = code_engine_service.get_status()
    projects = []
    pager = ProjectsPager(
        client=code_engine_service,
        limit=100,
    )
    while pager.has_next():
        next_page = pager.get_next()
        assert next_page is not None
        projects.extend(next_page)

    # Assuming projects is a list of dictionaries with 'name' and 'id' keys
    for project in projects:
        if project['name'] == project_name:
            return project['id']
    return None
    
def createBuildSecret(project_id):
    code_engine_service = ceClient()

    response = code_engine_service.create_secret(
        project_id=project_id,
        format='registry',
        name=f'{prefix}-us-icr-secret',
        data={
            'username': 'iamapikey',
            'password': ibmcloud_api_key,
            'server': 'us.icr.io',
        }
    )
    secret = response.get_result()

    return secret


def createNewBuild(project_id, buildSecretName):
    code_engine_service = ceClient()

    response = code_engine_service.create_build(
        project_id=project_id,
        name=f'{prefix}-build',
        output_image='private.us.icr.io/ce-projects-rst/image-name',
        output_secret=buildSecretName,
        source_url='https://github.com/IBM/CodeEngine',
        strategy_type='dockerfile',
    )
    build = response.get_result()

    print(json.dumps(build, indent=2))

def getSecrets(project_id):
    code_engine_service = ceClient()
    all_results = []
    pager = SecretsPager(
        client=code_engine_service,
        project_id=project_id,
        limit=100,
    )
    while pager.has_next():
        next_page = pager.get_next()
        assert next_page is not None
        all_results.extend(next_page)

    print(json.dumps(all_results, indent=2))

def getJobs(project_id):
    code_engine_service = ceClient()
    all_results = []
    pager = JobsPager(
        client=code_engine_service,
        project_id=project_id,
        limit=100,
    )
    while pager.has_next():
        next_page = pager.get_next()
        assert next_page is not None
        all_results.extend(next_page)

    print(json.dumps(all_results, indent=2))

@click.command()
@click.option('--project_name', prompt='Please enter the Code Engine project name', help='The name of the Code Engine project.')
def main(project_name):
    project_id = get_project_id(project_name)
    if project_id is not None:
        # allSecrets = getSecrets(project_id)
        getProjectJobs = getJobs(project_id)
        # newBuildSecret = createBuildSecret(project_id)
        # buildSecretName = newBuildSecret['name']
        # newBuild = createNewBuild(project_id, buildSecretName)
        # click.echo(f'Build secret created')
        # click.echo(buildSecretName)
    else:
        click.echo(f'No project found with the name {project_name}.')

if __name__ == '__main__':
    main()