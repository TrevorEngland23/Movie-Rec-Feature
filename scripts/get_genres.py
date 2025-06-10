from azure.storage.blob import BlobServiceClient
import os

def get_genre_names():
    account_name = "c964capstone1121312"
    sas_token = os.getenv("AZURE_SAS_TOKEN")

    account_url = f"https://{account_name}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=sas_token)

    container_name = "tmdbfilteredgenres"
    container_client = blob_service_client.get_container_client(container_name)

    genre_names = []
    for blob in container_client.list_blobs():
        if blob.name.endswith('.csv'):
            prefix = blob.name.rsplit('.', 1)[0]
            genre_names.append(prefix)
            genre_names_relevant = genre_names[2:]

    return genre_names_relevant