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
        card_id = event['queryStringParameters']['card_id']  # Assuming card_id is passed as a query parameter

        try:
            response = table.delete_item(
                Key={
                    'card_id': card_id
                }
            )
            return {
                'statusCode': 200,
                'body': json.dumps('Card deleted successfully')
            }

        except ClientError as e:
            error_message = str(e)
            print(f'ClientError: {error_message}')  # Print the error message
            return {
                'statusCode': 400,
                'body': json.dumps('Error deleting card')
            }

    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps('card_id parameter is missing')
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing the request: {str(e)}')
        }
