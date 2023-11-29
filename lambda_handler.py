import boto3
import requests
from google.cloud import storage
import json
from google.oauth2 import service_account
import json
import os
import logging
import base64
import datetime

def lambda_handler(event, context):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Extract submission URL and user email from the SNS message
    message_str = event['Records'][0]['Sns']['Message']
    logger.info("message_str: %s", message_str)
    
    # Parse the message string as JSON
    message = json.loads(message_str)
    logger.info("message: %s", message)

    # Extract submission_url and user_email
    attempts = int(message['attempts'])
    status=message['status']
    submission_url = message['submissionUrl']
    user_email = message['userEmail']
    assignment_id = message['assignmentId']
    errorMessage=message['errorMessage']
    logger.info("submission_url: %s", submission_url)
    logger.info("user_email: %s", user_email)
    logger.info("assignment_id: %s", assignment_id)
    logger.info("attempts : %d", attempts)

     

    google_creds_base64 = os.environ['GOOGLE_CREDENTIALS']
    google_creds_json = base64.b64decode(google_creds_base64).decode('utf-8')

    try:
        # Parse the JSON string into a dictionary
        google_creds = json.loads(google_creds_json)
    except json.JSONDecodeError as e:
        print("Error parsing JSON: ", e)
        logger.info("Error " + e)
        print("JSON string: ", google_creds_json)
        logger.info("GOOGLE_CREDENTIALS: JSON " + google_creds_json)
        raise

    # Google Cloud authentication
    credentials = service_account.Credentials.from_service_account_info(google_creds)
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(os.environ['GCP_BUCKET_NAME'])
    logger.info("GCP_BUCKET_NAME: " + os.environ['GCP_BUCKET_NAME'])
    source_email = os.environ.get('FROM_ADDRESS')
    logger.info("source_email : %s", source_email)
    

    try:
        if status == "SUCCESS":

            response = requests.get(submission_url)
            file_content = response.content
            response_content_type = response.headers.get('Content-Type')
            logger.info("Response Content-Type: %s", response_content_type)

            if response.status_code != 200 or not file_content:
                raise ValueError("Invalid URL or empty content")



            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            directory_path = f"{user_email}/{assignment_id}/"
            unique_file_name = f"submission_{timestamp}.zip"
            full_path = directory_path + unique_file_name
            blob = bucket.blob(full_path)
            blob.upload_from_string(file_content, content_type="application/zip")
            logger.info("full_path : %s", full_path)


            logger.info("Sending Email")
            # Send success email
            send_email(user_email,full_path, assignment_id, source_email,errorMessage, "Submission Received - Canvas",
                    "Your submission has been successfully received." )

            logger.info("Email Sent and updating dynamo DB")
            # Update DynamoDB
            update_dynamodb(user_email, assignment_id, submission_url, full_path, timestamp)
            # update_dynamodb(user_email, assignment_id, submission_url)

            logger.info("Table updated")
        else:
            raise ValueError("Non-success status received")

    except Exception as e:
        logger.error(f"Error in processing submission: {e}")
        send_email(user_email,"N/A", assignment_id, source_email, errorMessage,"Submission Error - Canvas",
                   "There was an error with your submission. Please check the submission rules")
        
        # update_dynamodb(user_email, assignment_id, submission_url, full_path, timestamp)
    

def send_email(user_email,full_path ,assignment_id, source_email,errorMessage, subject, body):
    # Send Email to the user
    ses_client = boto3.client('ses')
    email_body = f"""
    Dear {user_email},

    {errorMessage}

    {body}

    - Assignment ID: {assignment_id}
    - Submission Path: {full_path}
     
    Should you have any questions or need further assistance,
    please feel free to contact us at info@demo.supriyavallarapu.me. 

    We appreciate your effort and time.

    Best regards,
    Department of College of Engineering 
    """.format(user_email=user_email, full_path=full_path, assignment_id=assignment_id, errorMessage=errorMessage)


    ses_client.send_email(
        Source=source_email,
        Destination={'ToAddresses': [user_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': email_body}}
        }
    )

    
def update_dynamodb(user_email, assignment_id, submission_url, full_path, timestamp):
    table_name = os.environ.get('DYNAMO_TABLE_NAME')
    partition_key = f"{user_email}#{assignment_id}#{timestamp}"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.put_item(
        Item={
            'PartitionKey': partition_key,
            'AssignmentId': assignment_id,
            'SubmissionUrl': submission_url,
            'FilePath': full_path,
            'Timestamp':  timestamp
        }
    )



    
    
