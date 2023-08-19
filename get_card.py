import json
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from aws_lambda_powertools.utilities.parser import BaseModel, parse #Lembrar de adicionar o aws_lambda_powertools nas "Camadas" da aws Lambda

# Get DB connection parameters from environment variables
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')
REGION_NAME = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
table = dynamodb.Table(DYNAMODB_TABLE)

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
    linkedin: Optional[str]
    facebook: Optional[str]
    github: Optional[str]
    site: Optional[str]
    def validate_email(self, email: str) -> None:
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
        card_id = event['queryStringParameters'].get('card_id')  # Get the card_id from the query parameters
        if not card_id:
            return {
                'statusCode': 400,
                'body': json.dumps('Missing card_id parameter in the query')
            }

        response = table.get_item(
            Key={
                'card_id': card_id
            }
        )

        if 'Item' in response:
            user_data = UserData.parse_obj(response['Item'])
            return {
                'statusCode': 200,
                'body': json.dumps(user_data.dict())
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps('No user found for the provided card_id')
            }

    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing the request: {str(e)}')
        }
