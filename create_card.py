import json
import os
import re
import hashlib
import base64
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import List, Optional
from aws_lambda_powertools.utilities.parser import BaseModel, parse

# Get DB connection parameters from environment variables
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')
REGION_NAME = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')

dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
table = dynamodb.Table(DYNAMODB_TABLE)
s3 = boto3.client('s3')


class UserData(BaseModel):
    """
    Represents user data model.
    """
    nome: str
    email: str
    whatsapp: str
    card_id: str
    foto_perfil: Optional[str]
    formacao: Optional[str]
    cargo_atual: Optional[str]
    biografia: Optional[str]
    chave_pix: Optional[str]
    lattes: Optional[str]
    instagram: Optional[str]
    twitter: Optional[str]
    facebook: Optional[str]
    github: Optional[str]
    site: Optional[str]

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
    try:
        user_data = parse(event['body'], UserData)

        required_fields = ['nome', 'email', 'whatsapp', 'card_id']
        if not all(field in user_data.dict() for field in required_fields):
            return {
                'statusCode': 400,
                'body': json.dumps('Required user data is missing in the request')
            }

        if user_data.foto_perfil:
            # Extract base64 image data from Data URI
            user_data.foto_perfil = user_data.foto_perfil.split(",")[1]

            # Convert base64 string to bytes
            image_bytes = base64.b64decode(user_data.foto_perfil)

            # Upload the image to S3
            s3.put_object(Body=image_bytes, Bucket=S3_BUCKET, Key=user_data.card_id, ACL='public-read')

            # Get the URL of the image
            user_data.foto_perfil = f"https://{S3_BUCKET}.s3.amazonaws.com/{user_data.card_id}"

        try:
            response = table.put_item(
                Item=user_data.dict(),
                ConditionExpression='attribute_not_exists(card_id)'
            )
            return {
                'statusCode': 200,
                'body': json.dumps('User created successfully')
            }

        except ClientError as e:
            error_message = str(e)
            print(f'ClientError: {error_message}')  # Print the error message
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps('Duplicate entry exists.')
                }

        return {
            'statusCode': 400,
            'body': json.dumps('An unexpected error occurred')
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing the request: {str(e)}')
        }
