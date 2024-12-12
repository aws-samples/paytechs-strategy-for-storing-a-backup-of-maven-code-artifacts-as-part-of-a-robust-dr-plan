from typing import List
from os import environ
import boto3
import requests

# import local modules
from model.aws.code_artifact import Marshaller
from model.aws.code_artifact import AWSEvent
from model.aws.code_artifact import CodeArtifactChangeNotification

# Initialise outside of handler to avoid cold start
ca_client = boto3.client("codeartifact")
s3_client = boto3.client("s3")


def lambda_handler(event, context):  # pylint: disable=unused-argument
    """Entrypoint into the function"""
    # Deserialize event into strongly typed object
    aws_event: AWSEvent = Marshaller.unmarshall(event, AWSEvent)
    code_artifact_notification: CodeArtifactChangeNotification = aws_event.detail

    # Validate the detail type is correct
    if aws_event.detail_type != "CodeArtifact Package Version State Change":
        raise ValueError("This lambda only supports the CodeArtifact Package Version State Change event. Event used: " + aws_event.detail_type, event)

    # Only Maven packages are supported
    if code_artifact_notification.package_format != "maven":
        raise ValueError("This function only supports maven package format. Package format used: " + code_artifact_notification.package_format, event)


    # Construct the URL and headers to download the package
    authentication_header = get_user_authentication_header(code_artifact_notification.domain_name)
    package_locations = get_package_locations(code_artifact_notification)

    # This will be one jar file with the current implementation of CodeArtifact
    for package_location in package_locations:

        url = get_full_url(code_artifact_notification, aws_event, package_location)

        # Request the archive file from CodeArtifact
        get_archive_response = get_archive(url, authentication_header)
        if get_archive_response.status_code != 200:
            get_archive_response.raise_for_status()

        # Archive object to S3
        key = code_artifact_notification.domain_name + "/" + package_location
        put_object_response = put_object(get_archive_response.content, environ["DESTINATION_BUCKET"], key)

        status_code = put_object_response["ResponseMetadata"]["HTTPStatusCode"]
        if status_code != 200:
            raise ValueError("Message Failed with " + str(status_code) + " status code:", put_object_response)

        # Return event for further processing
        return Marshaller.marshall(aws_event)


def get_authorization_token(domain_name: str) -> dict:
    """Wrapper around boto3 codeartifact get_authorization_token api"""
    return ca_client.get_authorization_token(domain=domain_name)


def put_object(content: object, bucket: str, key:str) -> dict:
    """Wrapper around boto3 s3 client put_object api"""
    return s3_client.put_object(
        Body=content,
        Bucket=bucket,
        Key=key,
    )

def get_archive(url:str, authentication_header:requests.auth.HTTPBasicAuth) -> requests.Response:
    """Wrapper around request library get function"""
    return requests.get(url, auth=authentication_header, timeout=10)

def get_user_authentication_header(domain_name: str) -> requests.auth.HTTPBasicAuth:
    """Request a auth token from CodeArtifact to add to the user header"""
    auth_token_response = get_authorization_token(domain_name)

    if auth_token_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise ValueError(auth_token_response.text)

    return requests.auth.HTTPBasicAuth("aws", auth_token_response["authorizationToken"])


def list_package_version_assets(code_artifact_notification: CodeArtifactChangeNotification) -> requests.Response:
    """Get the artifact file name for this version of the package"""
    return ca_client.list_package_version_assets(
        domain=code_artifact_notification.domain_name,
        repository=code_artifact_notification.repository_name,
        format=code_artifact_notification.package_format,
        package=code_artifact_notification.package_name,
        packageVersion=code_artifact_notification.package_version,
        namespace=code_artifact_notification.package_namespace,
    )


def get_package_locations(code_artifact_notification: CodeArtifactChangeNotification) -> List[str]:
    """Use details from CodeArtifact to construct the package's location in CodeArtifact"""
    package_name = code_artifact_notification.package_name
    repository_name = code_artifact_notification.repository_name
    package_version = code_artifact_notification.package_version
    package_version_response = list_package_version_assets(code_artifact_notification)

    # Get the name of the whl file
    status_code = package_version_response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code != 200:
        raise ValueError("Message Failed with " + str(status_code) + " status code:", package_version_response)

    converted_package_namespace = "/".join(code_artifact_notification.package_namespace.split("."))
    package_locations = list(
        map(
            lambda asset: "/".join(
                ("maven", repository_name, converted_package_namespace, package_name, package_version, asset["name"])
            ),
            package_version_response["assets"],
        )
    )

    if not package_locations:
        raise ValueError("No assets found for " + package_name + " " + package_version)

    return package_locations


def get_full_url(code_artifact_notification: CodeArtifactChangeNotification, aws_event: AWSEvent, package_location: str) -> str:
    """Use details from CodeArtifact to construct the full URL to access CodeArtifact"""
    return "".join((
        "https://",
        code_artifact_notification.domain_name,
        "-",
        code_artifact_notification.domain_owner,
        ".d.codeartifact.",
        aws_event.region,
        ".amazonaws.com/",
        package_location,
    ))
