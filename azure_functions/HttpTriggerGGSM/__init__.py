import azure.functions as func
import json
import logging
from azure.storage.blob import BlobServiceClient
import os
import pandas as pd
import io
from azure.identity import DefaultAzureCredential

app = func.FunctionApp()

@app.function_name(name="HttpTriggerGGSM")
@app.route(route="HttpTriggerGGSM", auth_level=func.AuthLevel.ANONYMOUS)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    storage_account = os.getenv('STORAGE_ACCOUNT')
    logging.info(f"Storage account from env: {storage_account}")
    storage_container = os.getenv('STORAGE_CONTAINER')
    storage_base_url = f"https://{storage_account}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    genres = None
    
    try:
        req_body = req.get_json()
        genres = req_body.get('genres')
    except Exception as e:
        logging.error(f"Error parsing request body: {e}")
        genres = None

    if not genres:
        return func.HttpResponse("No genres receieved. Pass genres in request body as JSON.", status_code=400)
        
    blob_service_client = BlobServiceClient(account_url=storage_base_url, credential=credential)
    container_client = blob_service_client.get_container_client(storage_container)
    # find relevant datasets for each genre passed in the request
    # relevant_datasets = []

    image_base_url="https://image.tmdb.org/t/p/w300"
    results = {}
    for genre in genres:
        blob_name = f"{genre}.csv"
        try:
            blob_client = container_client.get_blob_client(blob_name)
            if blob_client.exists():
                blob_data = blob_client.download_blob().readall()
                df = pd.read_csv(io.BytesIO(blob_data))

                # Filter for valid vote_average, release_date, and runtime >= 30
                filtered_df = df[
                    df['title'].notna() &
                    df['vote_average'].notna() &
                    df['release_date'].notna() &
                    df['runtime'].notna()
                ]

                # Sample up to 20 from the filtered DataFrame
                random_twenty = filtered_df.sample(n=min(15, len(filtered_df)), random_state=None)
                movie_builder = []

                for _, row in random_twenty.iterrows():

                    poster_path = row.get("poster_path")
                    if pd.isna(poster_path) or not poster_path:
                        poster_path = f"https://{storage_account}.blob.core.windows.net/{storage_container}/defaultimage"
                    else:
                        poster_path = f"{image_base_url}{poster_path}"

                    vote_average = row.get("vote_average")
                    if float(vote_average).is_integer():
                        vote_average_formatted = int(vote_average)
                    else:
                        vote_average_formatted = round(float(vote_average), 1)

                    movie_builder.append({
                        "title": row.get("title", ""),
                        "poster_path": poster_path,
                        "vote_average": vote_average_formatted,
                        "release_date": row.get("release_date", ""),
                        "runtime": row.get("runtime", "")
                    })
                results[genre] = movie_builder
                logging.info(f"Selected {len(movie_builder)} movies for genre '{genre}'")
        except Exception as e:
            logging.error(f"Error accessing blob {blob_name}: {e}")

    if results:
        return func.HttpResponse(json.dumps(results), status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse("No datasets found for the provided genres.", status_code=404)


