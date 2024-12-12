import os
import unittest

import pytest
import requests

from artifact_backup import app
from model.aws.code_artifact import AWSEvent
from model.aws.code_artifact import CodeArtifactChangeNotification
from model.aws.code_artifact import Marshaller
from unittest import mock


def eventBridgeCodeArtifactEvent():
    """Generates EventBridge EC2 Instance Notification Event"""

    return {
        "account": "accountnumber",
        "detail": {
            "changes": {
                "assetsAdded": 0,
                "assetsRemoved": 0,
                "assetsUpdated": 0,
                "metadataUpdated": "false",
                "statusChanged": "true",
            },
            "domainName": "codeartifact-backup-domain",
            "domainOwner": "accountnumber",
            "eventDeduplicationId": "zh7q1uOww9K1skLhjA6A9PWD17IhEkLEM7zNtuDn2EY=",
            "operationType": "Updated",
            "packageFormat": "maven",
            "packageName": "internal-library",
            "packageNamespace": "com.amazonaws.app",
            "packageVersion": "1.0",
            "packageVersionRevision": "nQjAwhAz3hVCmCKLlcrxOsvCxBq844wgT+ZZjiXjFZo=",
            "packageVersionState": "Published",
            "repositoryAdministrator": "accountnumber",
            "repositoryName": "codeartifact-backup-repository",
            "sequenceNumber": 2,
        },
        "detail-type": "CodeArtifact Package Version State Change",
        "id": "f290946b-52b5-6e4c-1ef7-08347ae26732",
        "region": "us-east-1",
        "resources": [
            "arn:aws:codeartifact:us-east-1:accountnumber:package/codeartifact-backup-domain/codeartifact-backup-repository/maven/com.amazonaws.app/internal-library"
        ],
        "source": "aws.codeartifact",
        "time": "2024-07-23T11:55:55Z",
        "version": "0",
    }


def mocked_get_auth_token(domain):
    return {
        "authorizationToken": "auth-token",
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }


def mocked_get_auth_token_failure(domain):
    return {"ResponseMetadata": {"HTTPStatusCode": 401}}


def mocked_list_package_version_assets(code_artifact_notification):
    return {
        "ResponseMetadata": {"HTTPStatusCode": 200},
        "assets": [{"name": "internal-library-1.0.jar"}],
    }


def mocked_list_package_version_assets_failure(code_artifact_notification):
    return {"ResponseMetadata": {"HTTPStatusCode": 401}}


def mocked_put_object(content, bucket, key):
    return {"ResponseMetadata": {"HTTPStatusCode": 200}}


def mocked_put_object_failure(content, bucket, key):
    return {"ResponseMetadata": {"HTTPStatusCode": 401}}


def mocked_get_archive(URL, authentication_header):
    class RequestObject:
        status_code = 200
        content = ""

    return RequestObject()


def mocked_get_archive_failure(URL, authentication_header):
    class RequestObject:
        status_code = 401
        content = ""

    return RequestObject()


class MyTest(unittest.TestCase):

    

    def test_marshall(self):
        aws_event: AWSEvent = Marshaller.unmarshall(eventBridgeCodeArtifactEvent(), AWSEvent)
        detail: CodeArtifactChangeNotification = aws_event.detail
        assert detail.package_version == "1.0"

    @mock.patch(
        "artifact_backup.app.get_authorization_token",
        side_effect=mocked_get_auth_token,
    )
    def test_get_user_authentication_header(self, get_auth_mock):
        ret = app.get_user_authentication_header("domain")
        assert ret == requests.auth.HTTPBasicAuth("aws", "auth-token")

    @mock.patch(
        "artifact_backup.app.get_authorization_token",
        side_effect=mocked_get_auth_token_failure,
    )
    def test_get_user_authentication_header_auth_failure(self, get_auth_mock):
        with pytest.raises(Exception):
            app.get_user_authentication_header("domain")


    @mock.patch(
        "artifact_backup.app.list_package_version_assets",
        side_effect=mocked_list_package_version_assets,
    )
    def test_get_package_locations(self, describe_package_mock):
        aws_event: AWSEvent = Marshaller.unmarshall(eventBridgeCodeArtifactEvent(), AWSEvent)
        code_artifact_notification: CodeArtifactChangeNotification = aws_event.detail
        ret = app.get_package_locations(code_artifact_notification)
        assert ret == ["maven/codeartifact-backup-repository/com/amazonaws/app/internal-library/1.0/internal-library-1.0.jar"]

    @mock.patch(
        "artifact_backup.app.list_package_version_assets",
        side_effect=mocked_list_package_version_assets_failure,
    )
    def test_get_package_version_failure(self, get_package_version_mock):
        with pytest.raises(Exception):
            aws_event: AWSEvent = Marshaller.unmarshall(eventBridgeCodeArtifactEvent(), AWSEvent)
            code_artifact_notification: CodeArtifactChangeNotification = aws_event.detail
            app.get_package_locations(code_artifact_notification)

    def test_get_full_url(self):
        aws_event: AWSEvent = Marshaller.unmarshall(eventBridgeCodeArtifactEvent(), AWSEvent)
        code_artifact_notification: CodeArtifactChangeNotification = aws_event.detail
        ret = app.get_full_url(
            code_artifact_notification,
            aws_event,
            "maven/codeartifact-backup-repository/com/amazonaws/app/internal-library/1.0/internal-library-1.0.jar",
        )
        assert (
            ret
            == "https://codeartifact-backup-domain-accountnumber.d.codeartifact.us-east-1.amazonaws.com/maven/codeartifact-backup-repository/com/amazonaws/app/internal-library/1.0/internal-library-1.0.jar"
        )

    # Test lambda_handler when the packageFormat is pypi instead of maven
    def test_lambda_handler_fail_wrong_package_format(self):
        with pytest.raises(ValueError):
            event = eventBridgeCodeArtifactEvent()
            event["detail"]["packageFormat"] = "pypi"
            app.lambda_handler(event, "")

    # Test lambda_handler throws error when the detail-type isn't correct
    def test_lambda_handler_fail_wrong_detail_type(self):
        with pytest.raises(ValueError):
            event = eventBridgeCodeArtifactEvent()
            event["detail-type"] = "Wrong Detail Type"
            app.lambda_handler(event, "")


    @mock.patch(
        "artifact_backup.app.get_authorization_token",
        side_effect=mocked_get_auth_token,
    )
    @mock.patch(
        "artifact_backup.app.list_package_version_assets",
        side_effect=mocked_list_package_version_assets,
    )
    @mock.patch("artifact_backup.app.put_object", side_effect=mocked_put_object)
    @mock.patch("artifact_backup.app.get_archive", side_effect=mocked_get_archive)
    def test_lambda_handler(self, get_auth_mock, describe_package_mock, put_object_mock, request_mock):
        os.environ["DESTINATION_BUCKET"] = "FOO"
        ret = app.lambda_handler(eventBridgeCodeArtifactEvent(), "")

        awsEventRet: AWSEvent = Marshaller.unmarshall(ret, AWSEvent)
        detailRet: CodeArtifactChangeNotification = awsEventRet.detail

        assert detailRet.package_name == "internal-library"

    @mock.patch(
        "artifact_backup.app.get_authorization_token",
        side_effect=mocked_get_auth_token,
    )
    @mock.patch(
        "artifact_backup.app.list_package_version_assets",
        side_effect=mocked_list_package_version_assets,
    )
    @mock.patch("artifact_backup.app.put_object", side_effect=mocked_put_object)
    @mock.patch("artifact_backup.app.get_archive", side_effect=mocked_get_archive_failure)
    def test_lambda_handler_get_archive_failure(
        self, get_auth_mock, describe_package_mock, put_object_mock, request_mock
    ):
        with pytest.raises(Exception):
            os.environ["DESTINATION_BUCKET"] = "FOO"
            app.lambda_handler(eventBridgeCodeArtifactEvent(), "")

    @mock.patch(
        "artifact_backup.app.get_authorization_token",
        side_effect=mocked_get_auth_token,
    )
    @mock.patch(
        "artifact_backup.app.list_package_version_assets",
        side_effect=mocked_list_package_version_assets,
    )
    @mock.patch("artifact_backup.app.put_object", side_effect=mocked_put_object_failure)
    @mock.patch("artifact_backup.app.get_archive", side_effect=mocked_get_archive)
    def test_lambda_handler_put_object_failure(
        self, get_auth_mock, describe_package_mock, put_object_mock, request_mock
    ):
        with pytest.raises(Exception):
            os.environ["DESTINATION_BUCKET"] = "FOO"
            app.lambda_handler(eventBridgeCodeArtifactEvent(), "")
