import azure.functions as func
import datetime
import json
import logging
from azure.storage.blob import BlobServiceClient
import os
import pandas as pd
import io

app = func.FunctionApp()

@app.route(route="HttpTriggerGGSM", auth_level=func.AuthLevel.ANONYMOUS)

def HttpTriggerGGSM(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    genres = None
    
    try:
        req_body = req.get_json()
        genres = req_body.get('genres')
    except Exception as e:
        logging.error(f"Error parsing request body: {e}")
        genres = None

    if not genres:
        return func.HttpResponse("No genres receieved. Pass genres in request body as JSON.", status_code=400)
        
    account_url = "https://c964capstone1121312.blob.core.windows.net"
    azure_sas_token = os.getenv("AZURE_SAS_TOKEN")
    container_name = "tmdbfilteredgenres"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=azure_sas_token)
    container_client = blob_service_client.get_container_client(container_name)

    # find relevant datasets for each genre passed in the request
    # relevant_datasets = []
    results = {}
    for genre in genres:
        blob_name = f"{genre}.csv"
        try:
            blob_client = container_client.get_blob_client(blob_name)
            if blob_client.exists():
                blob_data = blob_client.download_blob().readall()
                df = pd.read_csv(io.BytesIO(blob_data))
                random_twenty = df.sample(n=min(20, len(df)), random_state=None)
                movie_titles = random_twenty['title'].tolist()
                # logging.info(f"Randomly selected 20 movies for {genre}: {random_twenty.to_dict(orient='records')}")
                results[genre] = movie_titles
                logging.info(f"Selected 20 movies for genre '{genre}': {movie_titles}")
                # results[genre] = random_twenty.to_dict(orient='records')
        except Exception as e:
            logging.error(f"Error accessing blob {blob_name}: {e}")

    if results:
        return func.HttpResponse(json.dumps(results), status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse("No datasets found for the provided genres.", status_code=404)


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