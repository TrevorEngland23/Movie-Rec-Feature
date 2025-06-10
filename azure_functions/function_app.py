import azure.functions as func
import datetime
import json
import logging

app = func.FunctionApp()

@app.route(route="HttpTriggerGGSM", auth_level=func.AuthLevel.ANONYMOUS)
def HttpTriggerGGSM(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    genres = None
    if req.method == 'GET':
        genres = req.params.get('genres')
    
    if not genres:
        try:
            req_body = req.get_json()
            genres = req_body.get('genres')
        except Exception as e:
            logging.error(f"Error parsing request body: {e}")
            genres = None

        if genres:
            logging.info(f"Received genres: {genres}")
            return func.HttpResponse(f"Received genres: {genres}", status_code=200)
        else:
            return func.HttpResponse("No genres receieved. Pass genres in request body as JSON.", status_code=400)

@app.route(route="HttpTriggerMovieRecs", auth_level=func.AuthLevel.ANONYMOUS)
def HttpTriggerMovieRecs(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )