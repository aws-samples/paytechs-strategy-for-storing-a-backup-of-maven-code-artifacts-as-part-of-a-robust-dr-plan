# PayTech's Strategy for storing a backup of maven code artifacts as part of a robust disaster recovery plan

This repository is a sample of how AWS customer PayTech leverages several AWS services to automatically backup Maven packages immediately after they are published to a CodeArtifact repository. The key components are:

**AWS CodeArtifact** - This is where the Maven packages are published initially by developers.

**AWS EventBridge** - An event rule is created that monitors for the PackageVersionPublished event from CodeArtifact. This triggers whenever a new Maven package version is published.

**AWS Lambda** - An Lambda function is invoked by the EventBridge rule. This function retrieves the published Maven package from CodeArtifact and uploads it to an S3 bucket for backup purposes.

**AWS S3** - A designated S3 bucket stores the backup copies of the published Maven packages.

The overall workflow is:

- Developer publishes a new Maven package version to a CodeArtifact repository
- The PackageVersionPublished event fires in EventBridge
- The EventBridge rule triggers the Lambda function
- The Lambda function downloads the published package from CodeArtifact
- The Lambda function uploads the package to the backup S3 bucket

By backing up published packages to S3 immediately, this tool enables quick recovery of any Maven packages that are accidentally or maliciously deleted from the CodeArtifact repository. The backups in S3 can be used to republish the deleted packages back to CodeArtifact.

# Table of Contents

## Dependencies

- [requests](https://pypi.org/project/requests/)
- [six](https://pypi.org/project/six/)
- [boto3](https://pypi.org/project/boto3/)

## Prerequisites

1. [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured with appropriate permissions.
2. [Python 3.12](https://www.python.org/downloads/) or later if you plan to use your IDE to detect problems in the code.
3. [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) for deployment.
4. [AWS CodeArtifact Domain and Repository](https://aws.amazon.com/codeartifact/) an existing domain and repository is required. The domain name and repository name can be entered as an input parameter during deployment.

## Overview

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. It includes the following files and folders.

- artifact_backup_function - Code for the application's Lambda function.
- events - Invocation events that you can use to invoke the function.
- assets - Files used for automated and manual testing. In this folder are two files, one binary named `internal-library-1.0.jar` and another named `assets/maven-metadata.xml`. They are only used for end to end tests. These files are not required to run the backup solution.
- tests - Unit tests for the application code. 
- template.yaml - A template that defines the application's AWS resources.

This application reacts to AWS CodeArtifact when a new version is published or an existing version is updated.

The application uses several AWS resources, including S3, a Lambda function and an EventBridge Rule trigger. These resources are defined in the `template.yaml` file in this project. You can update the template to add AWS resources through the same deployment process that updates your application code.

If you prefer to use an integrated development environment (IDE) to build and test your application, you can use the AWS Toolkit.  
The AWS Toolkit is an open source plug-in for popular IDEs that uses the SAM CLI to build and deploy serverless applications on AWS. The AWS Toolkit also adds a simplified step-through debugging experience for Lambda function code. See the following links to get started.

* [CLion](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [GoLand](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [WebStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [Rider](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PhpStorm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [RubyMine](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [DataGrip](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
* [Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html)

## Setup
1. Clone the repository:
   
```bash
$ git clone https://github.com/aws-samples/maven-package-backup
artifactbackup$ cd maven-package-backup
```

2. Install dependencies if you plan to use your IDE to detect problems in the code:

```bash
maven-package-backup$ pip install -r ./artifact_backup_function/requirements.txt
```

## Deploy the application

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda.

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)
* Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

```bash
maven-package-backup$ sam build --use-container
maven-package-backup$ sam deploy --guided
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. The default name is `artifactbackup`
* **AWS Region**: The AWS region you want to deploy your app to.
* **Parameter DomainName**: Your Existing AWS CodeArtifact domain name
* **Parameter RegistryName**: Your Existing AWS CodeArtifact registry name
* **Parameter DestinationBucketNamePrefix**: The prefix of the newly created Amazon S3 bucket to store backups. The account number and region will be added to ensure the bucket name is unique.
* **Parameter FunctionName**: The name of the newly create AWS Lambda Function
* **Parameter RuleName**: The name of the newly created Amazon EventBridge Rule
* **Parameter LambdaRoleName**: The name of the newly created AWS Lambda IAM Role
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

## Use the SAM CLI to build and test locally

Build your application with the `sam build --use-container` command.

```bash
artifactbackup$ sam build --use-container
```

The SAM CLI installs dependencies defined in `artifact_backup_function/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Set local variables for `ACCOUNT` to your account number and `REGION` to the region you are working in. The region below is set to `us-east-1` but you may need to change this depending on which region you've deployed to.

```bash
maven-package-backup$ ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
maven-package-backup$ REGION=us-east-1 # replace with a different region if required
```

In the `events/event.json` file, change the placeholder `<accountnumber>` to your account number and placeholder `<region>` to your region. The below command will make these replacements in the `events/event.json` file using the local variables set above.

```bash
maven-package-backup$ sed -i '' "s/<accountnumber>/$ACCOUNT/g" events/event.json
maven-package-backup$ sed -i '' "s/<region>/$REGION/g" events/event.json
```


Upload artifact `assets/internal-library-1.0.jar` to `codeartifact-repository` in `codeartifact-backup-domain`

```bash
maven-package-backup$ REGION=$REGION ACCOUNT=$ACCOUNT tests/integration/curl.sh
```

Set an environment variable file named `env.json` to define where your artifacts will be backed up to.

```bash
maven-package-backup$ echo '{"Parameters":{"DESTINATION_BUCKET":"artifact-backup-bucket-'$ACCOUNT'-'$REGION'"}}' > env.json
```

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project. Run functions locally and invoke them with the `sam local invoke` command.

```bash
maven-package-backup$ sam local invoke ArtifactBackupFunction --env-vars env.json --event events/event.json
```

## Add a resource to your application
The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
artifactbackup$ sam logs -n ArtifactBackupFunction --stack-name "artifactbackup" --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Tests

Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

```bash
artifactbackup$ pip install -r tests/requirements.txt --user
# unit test
artifactbackup$ python -m pytest tests/unit -v
# integration test, requiring deploying the stack fipython -m pytest tests/unit -vrst.
# Create the env variable AWS_SAM_STACK_NAME with the name of the stack we are testing
artifactbackup$ AWS_SAM_STACK_NAME="artifactbackup" python -m pytest tests/integration -v
```

## Cleanup

Delete the contents of the backup bucket and all object versions.

```bash
BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`BackupBucket`].OutputValue' --output text)
aws s3api delete-objects --bucket $BUCKET --delete "$(aws s3api list-object-versions --bucket $BUCKET --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"
aws s3api delete-objects --bucket $BUCKET --delete "$(aws s3api list-object-versions --bucket $BUCKET --query='{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')"
```

Delete all the other resources using the SAM CLI

```bash
sam delete --stack-name "artifactbackup"
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

