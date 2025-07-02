import pandas as pd
import os
import io
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
from azure.storage.blob import BlobServiceClient

# Source for guidance: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
# not ideal, but to avoid putting the model in either container will do it this way. No secrets are exposed.
storage_account = "c964capstone1121312"
storage_container = "tmdbfilteredgenres"
account_key = "<STORAGE_ACCOUNT_KEY>" 
storage_base_url = f"https://{storage_account}.blob.core.windows.net"

blob_service_client = BlobServiceClient(account_url=storage_base_url, credential=account_key)
container_client = blob_service_client.get_container_client(storage_container)

blob = "TMDB_original_movie_dataset_v11.csv"
blob_client = container_client.get_blob_client(blob)

all_movies_df = []
if blob_client.exists():
    blob_data = blob_client.download_blob().readall()
    df = pd.read_csv(io.BytesIO(blob_data))
    all_movies_df.append(df)
else:
    all_movies_df = []

# create a features column on the dataframe and train the model against the original dataset
all_movies_df = pd.concat(all_movies_df, ignore_index=True).drop_duplicates(subset=['title'])
all_movies_df = all_movies_df.fillna('')
all_movies_df['features'] = (
    df['genres'].str.replace(',', ' ').str.lower().fillna('') * 3 + ' ' +
    df['keywords'].str.replace(',', ' ').str.lower().fillna('') * 3 + ' ' +
    df['overview'].str.lower().fillna('') + ' ' +
    df['title'].str.lower().fillna('')
)


vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
vectorizer.fit(all_movies_df['features'])

joblib.dump(vectorizer, '../Azure-Functions/tfidf_vectorizer.joblib')
