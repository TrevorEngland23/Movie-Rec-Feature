import pandas as pd

df = pd.read_csv('../data/TMDB_original_movie_dataset_v11.csv')
# print(df.columns)

filtered_df = df[df['vote_average'] >= 7.5]
filtered_df = filtered_df.dropna(subset=['genres', 'title', 'vote_average', 'runtime'])
filtered_df = filtered_df[filtered_df['runtime'] >= 30]
filtered_df = filtered_df[filtered_df['original_language'].isin(['en', 'es'])]

# Attempt to remove pornographic content from the dataset... will also run images to openAI in attempt to hide pornographic material in images.
# Removed this line of code after creating the dataset to prevent foul language in source code. Only including these files to demonstrate how the dataset was cleaned and populated.

# porn_content_kws =  REDACTED
# filtered_df = filtered_df[
#     ~filtered_df['title'].str.contains(porn_content_kws, case=False, na=False) &
#     ~filtered_df['overview'].str.contains(porn_content_kws, case=False, na=False) &
#     ~filtered_df['keywords'].str.contains(porn_content_kws, case=False, na=False)
# ]
print (filtered_df.head())
filtered_df = filtered_df.sort_values(by='vote_average', ascending=False)
print(len(filtered_df))


filtered_df.to_csv('../data/TMDB_modified_movie_data.csv', index=False)
