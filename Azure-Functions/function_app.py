import azure.functions as func
from azure.identity import DefaultAzureCredential
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import base64
import json
import logging
from azure.storage.blob import BlobServiceClient
import os
import pandas as pd
import io
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = func.FunctionApp()

credential = DefaultAzureCredential()
storage_account = os.getenv("STORAGE_ACCOUNT")
storage_container = os.getenv("STORAGE_CONTAINER")
storage_base_url = f"https://{storage_account}.blob.core.windows.net"

@app.route(route="HttpTriggerGGSM", auth_level=func.AuthLevel.ANONYMOUS)
def HttpTriggerGGSM(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')


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


@app.route(route="HttpTriggerMovieRecs", auth_level=func.AuthLevel.ANONYMOUS)
def HttpTriggerMovieRecs(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        selected_movies = req_body.get('movies', [])
        original_user_selected_genres = req_body.get('genres', [])
        # print(original_user_selected_genres)
    except Exception as e:
        logging.error(f"Error parsing request body: {e}")
        return func.HttpResponse("Invalid request body.", status_code=400)

    if not selected_movies:
        return func.HttpResponse("No movies received from request body. Pass movies in request body as JSON.", status_code=400)
    
    image_base_url="https://image.tmdb.org/t/p/w300"
    blob_service_client = BlobServiceClient(account_url=f"https://{storage_account}.blob.core.windows.net", credential=credential)
    container_client = blob_service_client.get_container_client(storage_container)

    # Get ALL datasets in the container and compute cosine similarity
    all_movies = []
    for blob in container_client.list_blobs():
        if blob.name.endswith('.csv'):
            blob_client = container_client.get_blob_client(blob.name)
            blob_data = blob_client.download_blob().readall()
            df = pd.read_csv(io.BytesIO(blob_data))
            all_movies.append(df)

        if not all_movies:
            return func.HttpResponse(f"No datasets found at {storage_base_url}/{storage_container}.", status_code=404)
        all_movies_df = pd.concat(all_movies, ignore_index=True).drop_duplicates(subset=['title'])

        genre_counts = all_movies_df['genres'].str.split(',').explode().str.strip().value_counts()

        plt.style.use('dark_background')
        plt.figure(figsize=(10, 5))
        sns.barplot(x=genre_counts.index, y=genre_counts.values, palette='mako')
        plt.xticks(rotation=45)
        plt.title('Number of Movies per Genre')
        plt.ylabel('Movie count')
        plt.xlabel('Genre')

        total_movies = genre_counts.sum()
        plt.text(
            0.95, 0.95, f"Total movies: {total_movies}", 
            horizontalalignment='right',
            verticalalignment='top',
            transform=plt.gca().transAxes,
            fontsize=10, color='gray'
        )

        buf1 = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf1, format='png')
        buf1.seek(0)
        genre_bar_chart = base64.b64encode(buf1.read()).decode('utf-8')
        plt.close()



        # Use genres and keywords to create a features column (customize this)
        all_movies_df['id'] = all_movies_df['id'].astype(str)
        selected_movies = [str(mid) for mid in selected_movies]
        all_movies_df['features'] = all_movies_df['genres'].fillna('') * 3 + ' ' + all_movies_df['keywords'].fillna('') * 3 + all_movies_df['overview'].fillna('')

        all_movies_df = all_movies_df.reset_index(drop=True)

        # Vectorize the features
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf_vectorizer.fit_transform(all_movies_df['features'])

        # Indicies of selected movies
        selected_indicies = all_movies_df[all_movies_df['title'].isin(selected_movies)].index.tolist()

        selected_genres = all_movies_df.loc[selected_indicies]['genres'].dropna().str.split(',').explode().str.strip().str.lower()

        user_selected_genres_lower = [g.lower() for g in original_user_selected_genres]
        filtered_genres = selected_genres[selected_genres.isin(user_selected_genres_lower)]
        # all_genres = all_movies_df['genres'].dropna().str.split(',').explode().str.strip()

        genre_count = filtered_genres.value_counts()
        if not genre_count.empty:

            plt.style.use('dark_background')
            pie_labels = [label.capitalize() for label in genre_count.index.tolist()]
            pie_sizes = genre_count.values
            plt.figure(figsize=(6, 6))
            colors = ["#EFE17B9F", '#2F4F4F',"#223767BD", '#696969', '#800000', '#DC143C']
            plt.pie(pie_sizes, labels=pie_labels, autopct='%1.1f%%', startangle=140, colors=colors)
            plt.title("Genre Breakdown of Liked Movies")
            buf2 = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf2, format='png')
            buf2.seek(0)
            genre_pie_chart = base64.b64encode(buf2.read()).decode('utf-8')
            plt.close()
        else:
            genre_pie_chart = None

     
        
        # Compute cosine similarity between selected movies and all movies
        selected_tfidf_matrix = tfidf_matrix[selected_indicies]
        cosine_sim = cosine_similarity(selected_tfidf_matrix, tfidf_matrix)
        top_recommendations = cosine_sim.mean(axis=0)

        # Exclude selected movies from recommendations
        all_movies_df['similarity'] = top_recommendations
        recs = all_movies_df[~all_movies_df['title'].isin(selected_movies)]
        # Allow 20 here in case some are filtered out for not having relevant data
        top_20_matches = recs.sort_values(by='similarity', ascending=False).head(20)

        cosine_scores = []
        rec_builder = []
        movie_count = 0

        for _,row in top_20_matches.iterrows():
            movie_id = row.get("id")
            title = row.get("title")
            poster_path = row.get("poster_path")
            vote_average = row.get("vote_average")
            release_date = row.get("release_date")
            runtime = row.get("runtime")
            overview = row.get("overview")
            genre = row.get("genres")

            if pd.isna(title) or pd.isna(poster_path) or pd.isna(vote_average) or pd.isna(release_date) or pd.isna(runtime) or pd.isna(overview) or pd.isna(genre):
                continue
            if not all([str(title).strip(), str(poster_path).strip(), str(release_date).strip(), str(overview).strip(), str(genre).strip()]):
                continue

            try:
                if pd.isna(poster_path) or not poster_path:
                    poster_path = f"https://{storage_account}.blob.core.windows.net/{storage_container}/defaultimage"
                else:
                    poster_path = f"{image_base_url}{poster_path}"
            except:
                logging.warning("No default image was found in the storage account.")

            
            try:
                if float(vote_average).is_integer():
                    vote_average_formatted = int(vote_average)
                else:
                    vote_average_formatted = round(float(vote_average), 1)
            except:
                logging.warning("'vote_average' is not of type float, int, or na")


            rec_builder.append({
                "id": movie_id,
                "title": title,
                "poster_path": poster_path,
                "vote_average": vote_average_formatted,
                "release_date": release_date,
                "runtime": runtime,
                "overview": overview,
                "homepage": row.get("homepage", ""),
                "genre": genre
            })

            cosine_scores.append(row.get("similarity"))
            movie_count += 1
            if movie_count == 10:
                break

        plt.style.use('dark_background')
        plt.figure(figsize=(8, 4))
        plt.plot(cosine_scores, color='gold', linestyle='--', alpha=0.5)
        plt.scatter(range(len(cosine_scores)), cosine_scores, color='darkviolet')
        plt.title("Cosine Similarity of Recommended Movies to Liked Movies", fontsize=12)
        plt.xlabel("Movie Recommendation #")
        plt.ylabel("Similarity Score")
        plt.grid(True)

        buf3 = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf3, format='png')
        buf3.seek(0)
        cosine_chart = base64.b64encode(buf3.read()).decode('utf-8')
        plt.close()
        # Return top 10 recommended movie titles
        rec_movies = rec_builder
        print(rec_movies)
        return func.HttpResponse(json.dumps({"recommended_movies": rec_movies, "genre_bar_chart": genre_bar_chart, "genre_pie_chart": genre_pie_chart, "cosine_similarity_chart": cosine_chart}), status_code=200, mimetype="application/json")
    
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )