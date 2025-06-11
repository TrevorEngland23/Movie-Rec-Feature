import azure.functions as func
import datetime
import json
import logging
from azure.storage.blob import BlobServiceClient
import os
import pandas as pd
import io
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
app = func.FunctionApp()

STORAGE_ACCOUNT = "c964capstone1121312"
STORAGE_CONTAINER = "tmdbfilteredgenres"
STORAGE_BASE_URL = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
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
        
    # account_url = "https://c964capstone1121312.blob.core.windows.net"
    azure_sas_token = os.getenv("AZURE_SAS_TOKEN")
    # container_name = "tmdbfilteredgenres"
    blob_service_client = BlobServiceClient(account_url=STORAGE_BASE_URL, credential=azure_sas_token)
    container_client = blob_service_client.get_container_client(STORAGE_CONTAINER)

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

    selected_movies = None
    try:
        req_body = req.get_json()
        selected_movies = req_body.get('movies')
    except Exception as e:
        logging.error(f"Error parsing request body: {e}")
        selected_movies = None

    if not selected_movies:
        return func.HttpResponse("No movies received from request body. Pass movies in request body as JSON.", status_code=400)
    
    # account_url = "https://c964capstone1121312.blob.core.windows.net"
    azure_sas_token = os.getenv("AZURE_SAS_TOKEN")
    # container_name = "tmdbfilteredgenres"
    blob_service_client = BlobServiceClient(account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net", credential=azure_sas_token)
    container_client = blob_service_client.get_container_client(STORAGE_CONTAINER)

    # Get ALL datasets in the container and compute cosine similarity
    all_movies = []
    for blob in container_client.list_blobs():
        if blob.name.endswith('.csv'):
            blob_client = container_client.get_blob_client(blob.name)
            blob_data = blob_client.download_blob().readall()
            df = pd.read_csv(io.BytesIO(blob_data))
            all_movies.append(df)
        if not all_movies:
            return func.HttpResponse(f"No datasets found at {STORAGE_BASE_URL}/{STORAGE_CONTAINER}.", status_code=404)
        all_movies_df = pd.concat(all_movies, ignore_index=True).drop_duplicates(subset=['title'])
    
        # Use genres and keywords to create a features column (customize this)
        all_movies_df['features'] = all_movies_df['genres'].fillna('') + ' ' + all_movies_df['keywords'].fillna('')

        # Vectorize the features
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf_vectorizer.fit_transform(all_movies_df['features'])

        # Indicies of selected movies
        selected_indicies = all_movies_df[all_movies_df['title'].isin(selected_movies)].index.tolist()
        if not selected_indicies:
            return func.HttpResponse("Selected movies not found in the dataset.", status_code=404)
        
        # Compute cosine similarity between selected movies and all movies
        selected_tfidf_matrix = tfidf_matrix[selected_indicies]
        cosine_sim = cosine_similarity(selected_tfidf_matrix, tfidf_matrix)
        top_recommendations = cosine_sim.mean(axis=0)

        # Exclude selected movies from recommendations
        all_movies_df['similarity'] = top_recommendations
        recs = all_movies_df[~all_movies_df['title'].isin(selected_movies)]
        new_top_recs = recs.sort_values(by='similarity', ascending=False).head(10)

        # Return top 10 recommended movie titles
        rec_movie_titles = new_top_recs['title'].tolist()
        print(rec_movie_titles)
        return func.HttpResponse(json.dumps({"recommended_movies": rec_movie_titles}), status_code=200, mimetype="application/json")
    
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )