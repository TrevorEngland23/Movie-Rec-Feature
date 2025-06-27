from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import os
import pandas as pd
import io

# Global variable to handle caching (images and titles won't change so not necessary to fetch them with every refresh / visit to page)
cached_genre_data = None
def get_genre_names_and_image():

    # If data is in the cache, use it and skip this logic. Much faster.
    # Note: If you store this data locally it's obviously the fastest option, but this way simulates the start of a session and fetching data from a backend.
    global cached_genre_data
    if cached_genre_data is not None:
        return cached_genre_data
    # Account Information
    credential = DefaultAzureCredential()
    account_name = os.getenv("STORAGE_ACCOUNT")
    account_url = f"https://{account_name}.blob.core.windows.net"
    container_name = os.getenv("STORAGE_CONTAINER")

    # Blob service client
    blob_service_client = BlobServiceClient(account_url=account_url, credential=credential) 
    container_client = blob_service_client.get_container_client(container_name)

    # Get genre names with image.
    genre_names = []
    genre_images = {}
    for blob in container_client.list_blobs():
        if blob.name.endswith('.csv'):
            prefix = blob.name.rsplit('.', 1)[0]
            genre_names.append(prefix)
            genre_names_relevant = genre_names[2:]
    
    for genre in genre_names_relevant:
        blob_name = f"{genre}.csv"
        try:
            blob_client = container_client.get_blob_client(blob_name)
            if blob_client.exists():
                blob_data = blob_client.download_blob().readall()
                df = pd.read_csv(io.BytesIO(blob_data))
                relevant_df = df[df['backdrop_path'].notnull() & df['backdrop_path'].str.strip().ne("")]
                if not relevant_df.empty:
                    backdrop_path = relevant_df.iloc[1].get("backdrop_path")
                    genre_images[genre] = backdrop_path
                    
        except Exception as e:
            print(f"No data found in {genre}.csv")

    # Cache the data since it will not change
    cached_genre_data = genre_images
    return genre_images