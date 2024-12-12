import logging
import os
from pprint import pprint
from time import sleep
from typing import List
from unittest import TestCase
from requests import put
from requests.auth import HTTPBasicAuth

import boto3
from botocore.exceptions import ClientError


class TestCodeArtifactEvent(TestCase):
    """
    This integration test will upload the maven package `assets/internal-library-1.0.jar`
    to the CodeArtifact repository and verify that the package was updated. 
    """

    codeartifact_client: boto3.client
    cloudformation_client: boto3.client
    s3_client: boto3.client
    sts_client: boto3.client

    @classmethod
    def get_and_verify_stack_name(cls) -> str:
        '''Verify environment variable is set'''
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")
        if not stack_name:
            raise ValueError(
                "Cannot find env var AWS_SAM_STACK_NAME. \n"
                "Please setup this environment variable with the stack name where we are running integration tests."
            )

        # Verify stack exists
        try:
            cls.cloudformation_client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise ValueError(
                f"Cannot find stack {stack_name}. \n" f'Please make sure stack with the name "{stack_name}" exists.'
            ) from e

        return stack_name

    @classmethod
    def setUpClass(cls) -> None:
        '''Configure class properties and populate registry to trigger event'''
        
        cls.codeartifact_client = boto3.client("codeartifact")
        cls.cloudformation_client = boto3.client("cloudformation")
        cls.s3_client = boto3.client("s3")
        cls.sts_client = boto3.client("sts")

        stack_name = TestCodeArtifactEvent.get_and_verify_stack_name()

        # Get resources from stack to use for verification
        cloudformation_paginator = cls.cloudformation_client.get_paginator("list_stack_resources")
        page_iterator = cloudformation_paginator.paginate(StackName=stack_name)
        resources = []
        for page in page_iterator:
            resources.extend(page["StackResourceSummaries"])

        # Get stack outputs
        describe_stacks_paginator = cls.cloudformation_client.get_paginator("describe_stacks")
        parameters = []
        for page in describe_stacks_paginator.paginate(StackName=stack_name):
            parameters.extend(page["Stacks"][0]['Parameters'])


        cls.domain_name = cls._get_parameter_value("DomainName", parameters)
        cls.repository_name = cls._get_parameter_value("RepositoryName", parameters)
        cls.function_name = cls._get_physical_resource_id("ArtifactBackupFunction", resources)
        cls.bucket_name = cls._get_physical_resource_id("DestinationBucket", resources)

        logging.info(cls.function_name, cls.domain_name, cls.repository_name, cls.bucket_name)

        # Add Maven package to CodeArtifact and Publish
        basic_auth = cls._get_basic_auth()
        with open("assets/internal-library-1.0.jar", "rb") as f:
            response = put(
                cls._get_url_domain() + cls._get_package_location(),
                data=f,
                auth=basic_auth,
                headers={"Content-Type": "application/octet-stream"},
                timeout=10,
            )
            f.close()
            with open("assets/maven-metadata.xml", "rb") as f:
                response = put(
                    cls._get_url_domain() + cls._get_metadata_location(),
                    data=f,
                    auth=basic_auth,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=10,
                )
                print(response.text)
                f.close()

    @classmethod
    def _get_physical_resource_id(cls, logical_resource_id: str, resources) -> str:
        # Find the logical resource id in CloudFormation stack
        # Return the physical resource id
        # Raise exception if not found
        service_resources = [resource for resource in resources if resource["LogicalResourceId"] == logical_resource_id]
        if not service_resources:
            raise ValueError(f"Cannot find {logical_resource_id}")

        return service_resources[0]["PhysicalResourceId"]

    
    @classmethod
    def _get_parameter_value(cls, parameter_key: str, parameters: List[dict]) -> str:
        # Find the parameter key in CloudFormation stack
        # Return the parameter value
        # Raise exception if not found
        parameters = [parameter for parameter in parameters if parameter["ParameterKey"] == parameter_key]
        if not parameters:
            raise ValueError(f"Cannot find {parameter_key}")

        return parameters[0]["ParameterValue"]
    


    @classmethod
    def tearDownClass(cls) -> None:
        cls.codeartifact_client.delete_package_versions(
            domain=cls.domain_name,
            repository=cls.repository_name,
            format="maven",
            package="internal-library",
            versions=["1.0"],
            namespace="com.amazonaws.app",
        )

        cls.s3_client.delete_object(
            Bucket=cls.bucket_name,
            Key=cls._get_bucket_key(),
        )

    def test_codeartifact_event(self):
        """Test codeartifact event"""
        retries = 5
        while retries >= 0:
            # use the lastest one
            backup_stored = self._is_backup_stored()
            if backup_stored:
                return

            logging.info("Backup is not stored yet, waiting")
            retries -= 1
            sleep(5)

        self.fail("Cannot find backup after 5 retries")

    @classmethod
    def _is_backup_stored(cls):
        """Check if backup is stored"""
        s3_client = boto3.client("s3")
        key = cls._get_bucket_key()

        try:
            s3_client.head_object(Bucket=cls.bucket_name, Key=key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                pprint(e)
                return False

            raise e
        except Exception as e:
            pprint(e)
            raise e

        return True

    @classmethod
    def _get_bucket_key(cls):
        """Return the bucket key that stores the backup"""
        return "/".join(
            (
                cls.domain_name,
                "maven",
                cls.repository_name,
                "com/amazonaws/app",
                "internal-library",
                "1.0",
                "internal-library-1.0.jar",
            )
        )

    @classmethod
    def _get_url_domain(cls):
        """Return the codeartifact domain url"""
        return "".join(
            (
                "https://",
                cls.domain_name,
                "-",
                cls.sts_client.get_caller_identity()["Account"],
                ".d.codeartifact.",
                "us-east-1",
                ".amazonaws.com/",
            )
        )

    @classmethod
    def _get_package_location(cls):
        """Return the location of the package"""
        return "/".join(
            ("maven", cls.repository_name, "com/amazonaws/app", "internal-library", "1.0", "internal-library-1.0.jar")
        )

    @classmethod
    def _get_metadata_location(cls):
        return "/".join(("maven", cls.repository_name, "com/amazonaws/app", "internal-library", "maven-metadata.xml"))

    @classmethod
    def _get_basic_auth(cls):
        # Get authorisation token from codeartifact
        domain_owner = cls.sts_client.get_caller_identity()["Account"]
        auth_token = cls.codeartifact_client.get_authorization_token(
            domain=cls.domain_name,
            domainOwner=domain_owner,
            durationSeconds=900,
        )["authorizationToken"]

        return HTTPBasicAuth("aws", auth_token)
    

