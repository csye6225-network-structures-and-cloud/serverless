import boto3
import requests
from google.cloud import storage
import json
from google.oauth2 import service_account
import json
import os

def lambda_handler(event, context):
    # Extract submission URL and user email from the SNS message
    message = event['Records'][0]['Sns']['Message']
    submission_url = message['submission_url']
    user_email = message['user_email']
    print(submission_url, user_email)

    # Downloading release 
    response = requests.get(submission_url)
    file_content = response.content

    # Google Cloud authentication
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(os.environ['GOOGLE_CREDENTIALS'])
    )
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(os.environ['GCP_BUCKET_NAME'])
    
    blob = bucket.blob('filename.zip')
    blob.upload_from_string(file_content)

    # Send Email to the user
    ses_client = boto3.client('ses')
    ses_client.send_email(
        Source='FROM_ADDRESS',
        Destination={'ToAddresses': [user_email]},
        Message={
            'Subject': {'Data': 'Submission Received - Canvas'},
            'Body': {'Text': {'Data': """Dear {user_email}, 
                              We have successfully received and processed your submission. 
                              Your Submission URL is : {submission_url}
                              Your file is now securely stored in our systems for further processing. We will send you an update once the processing is complete. 
                              Please feel free to contact us at info@demo.supriyavallarapu.me if you have any questions. We appreciate your time!"""}}
        }
    )

    # Update DynamoDB with email sent information
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('dynamo_table')
    table.put_item(
        Item={
            'Emailid': user_email,
            'submission_url': submission_url,
            'timestamp': str(context.aws_request_id)
        }
    )
