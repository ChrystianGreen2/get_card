# Melhorias
# Adicionar a Validação de Email no login tambem.
# Usar o bcrypt para encriptação das senhas
# Validação da senha com base em alguma regra


import json
import os
import hashlib
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from aws_lambda_powertools.utilities.parser import BaseModel, parse
import re

# Get DB connection parameters from environment variables
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')
REGION_NAME = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
table = dynamodb.Table(DYNAMODB_TABLE)


class LoginData(BaseModel):
    """
    Represents login data model.
    """
    email: str
    password: str


def lambda_handler(event: dict, context: dict) -> dict:
    """
    This function receives an API Gateway event, handles the request, and returns responses.

    Args:
        event (dict): Event data.
        context (dict): Context data.

    Returns:
        dict: Response data.
    """
    if 'body' in event:
        try:
            login_data = parse(event['body'], LoginData)
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid request body')
            }

        # Check if required fields are in login_data
        required_fields = ['email', 'password']
        if not all(field in login_data.dict() for field in required_fields):
            return {
                'statusCode': 400,
                'body': json.dumps('Required login data is missing in the request')
            }

        login_data_dict = login_data.dict()

        # Hash password
        hashed_password = hashlib.sha256(login_data_dict['password'].encode('utf-8')).hexdigest()
        login_data_dict['password'] = hashed_password

        try:
            response = table.get_item(
                Key={'email': login_data_dict['email']}
            )
        except ClientError as e:
            print("Unexpected error:", str(e))
            return {
                'statusCode': 500,
                'body': json.dumps('An unexpected error occurred')
            }

        if 'Item' in response:
            user = response['Item']
            if user['password'] == login_data_dict['password']:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': 'Login realizado com sucesso. Redirecionando para a tela inicial.',
                        'card_id': user['card_id']
                    })
                }

        # Invalid credentials
        return {
            'statusCode': 401,
            'body': json.dumps({'message': 'Credenciais inválidas. Verifique seu email e senha.'})
        }

    return {
        'statusCode': 400,
        'body': json.dumps('An unexpected error occurred')
    }
