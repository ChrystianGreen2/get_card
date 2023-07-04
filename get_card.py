import json
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Get DB connection parameters from environment variables
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')
REGION_NAME = os.getenv('AWS_REGION')

dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
table = dynamodb.Table(DYNAMODB_TABLE)


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
            return {
                'statusCode': 200,
                'body': json.dumps(response['Item'])
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
