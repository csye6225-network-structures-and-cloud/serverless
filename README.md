# serverless

## Lambda Function for Submission Processing
### Overview
This Lambda function is designed to automate the process of handling submissions. It is triggered by SNS notifications and performs the following actions:

- Downloads a submission from a provided URL.
- Stores the submission in a Google Cloud Storage Bucket.
- Sends an email to the user to inform them about the status of their submission.
- Logs the action details in a DynamoDB table.
  
### Prerequisites
- AWS account with infra and Lambda, SNS, and DynamoDB services using pulumi.
- Google Cloud account with a storage bucket.
- boto3 and google-cloud-storage libraries.
- Access to an SES (Simple Email Service) for sending emails.
  
### Environment Variables
Set the following environment variables in your Lambda function:

- GOOGLE_CREDENTIALS: Base64 encoded Google Cloud credentials.
- GCP_BUCKET_NAME: Name of your Google Cloud Storage bucket.
- FROM_ADDRESS: The email address used for sending notifications.

### Deployment
- Upload the Python zip file with dependencies to the to AWS Lambda function in pulumi.
- Set the required environment variables.
- Configure the SNS topic to trigger this Lambda function.
- Ensure the Lambda function has the necessary permissions for S3, DynamoDB, SES, and Google Cloud Storage.
  
### Usage
The function is automatically triggered by an SNS notification. Ensure that the message sent to the SNS topic contains the following fields:

- submissionUrl: URL of the submission to be downloaded.
- userEmail: Email address of the user.
- assignmentId: ID of the assignment.
- attempts: Number of attempts made.
- status: Status of the submission (e.g., "SUCCESS"/"FAILED").
- errorMessage: Error message if any.
  
### Function Details
- lambda_handler: The main handler for the Lambda function. It processes the SNS message, downloads the submission, stores it in Google Cloud Storage, sends an email to the user, and updates DynamoDB.
- send_email: Sends an email to the user with the status of their submission.
- update_dynamodb: Updates a DynamoDB table with the details of the action performed.
  
### Logging
- The function uses Python's logging module to log information and errors. Check the CloudWatch logs for debugging.
