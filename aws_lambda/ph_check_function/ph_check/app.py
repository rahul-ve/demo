import logging
import json
import ph_check  as pp
import traceback

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    logger.info(str(event))
    print(str(event))

    try:
        # From the input parameter named "event", get the body, dict
        event_body = event["body"]

        # Convert the input from a JSON string into a JSON object.
        req_body = json.loads(event_body)

        print(req_body)
        
    except ValueError:
        logger.error(traceback.format_exc())
        return { "statusCode": 400, "body": "Invalid Request Input!!" }
    else:
        number = req_body.get('number', '')
        country = req_body.get('country', 'AU')

        try:
            checked = pp.check_ph(number, country)
        except Exception as ee:
            logging.error("ph_check module encountered an error!")
            raise
        else:
            return {  "statusCode": 200,   "body": json.dumps(checked)     }

