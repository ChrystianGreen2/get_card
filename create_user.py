import json
import os
import hashlib
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import uuid
from aws_lambda_powertools.utilities.parser import BaseModel, parse
import re

# Get DB connection parameters from environment variables
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')
REGION_NAME = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
table = dynamodb.Table(DYNAMODB_TABLE)


class UserData(BaseModel):
    """
    Represents user data model.
    """
    name: str
    email: str
    password: str
    card_id: str

    def validate_email(self, email: str) -> None:
        """
        Validates the email format.

        Args:
            email (str): Email address.

        Raises:
            ValueError: If the email format is invalid.
        """
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")


def lambda_handler(event: dict, context: dict) -> dict:
    """
    This function receives an API Gateway event, handles the request, and returns responses.

    Args:
        event (dict): Event data.
        context (dict): Context data.

    Returns:
        dict: Response data.
    """
    print(event)
    if 'body' in event:
        try:
            user_data = parse(event['body'], UserData)
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid request body')
            }

        try:
            user_data.validate_email(user_data.email)
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid email format')
            }

        # Check if required fields are in user_data
        required_fields = ['name', 'email', 'password', 'card_id']
        if not all(field in user_data.dict() for field in required_fields):
            return {
                'statusCode': 400,
                'body': json.dumps('Required user data is missing in the request')
            }

        user_data_dict = user_data.dict()
        user_data_dict['email'] = user_data_dict.pop('email')  # Move 'id' value to 'email' key

        hashed_password = hashlib.sha256(user_data_dict['password'].encode('utf-8')).hexdigest()
        user_data_dict['password'] = hashed_password

        try:
            response = table.put_item(
                Item=user_data_dict,
                ConditionExpression='attribute_not_exists(email) and attribute_not_exists(phone) and attribute_not_exists(card_id)'
            )

            return {
                'statusCode': 200,
                'body': json.dumps('User created successfully')
            }

        except ClientError as e:
            # Handle integrity error more specifically
            error_message = str(e)
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps('Duplicate entry exists.')
                }
            else:
                print("Unexpected error:", error_message)
                return {
                    'statusCode': 500,
                    'body': json.dumps('An unexpected error occurred')
                }

    return {
        'statusCode': 400,
        'body': json.dumps('An unexpected error occurred')
    }
