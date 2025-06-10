import pandas as pd

df = pd.read_csv('../data/TMDB_original_movie_dataset_v11.csv')
# print(df.columns)

filtered_df = df[df['vote_average'] >= 7.5]
filtered_df = filtered_df.dropna(subset=['genres'])
filtered_df = filtered_df.sort_values(by='vote_average', ascending=False)
print(len(filtered_df))


filtered_df.to_csv('../data/TMDB_modified_movie_data.csv', index=False)
