import logging
import json
from . import ph_check  as pp
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid Request Input!!", status_code = 400)
    else:
        number = req_body.get('number', '')
        country = req_body.get('country', 'AU')

        try:
            checked = pp.check_ph(number, country)
        except Exception as ee:
            logging.error("ph_check module encountered an error!")
            raise
        else:
            return func.HttpResponse(json.dumps(checked), status_code=200)
    
