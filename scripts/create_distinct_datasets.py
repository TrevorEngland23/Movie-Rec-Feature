import pandas as pd

df = pd.read_csv('../data/TMDB_modified_movie_data.csv')

genre_lists = df['genres'].apply(lambda x: x.split(','))
stripped_genre_lists = genre_lists.apply(lambda genres: [g.strip() for g in genres])
all_genres = stripped_genre_lists.explode() #transforms the lists into flat structure
distinct_genres = all_genres.unique()

# for each genre, if the current data's genre column contains THIS genre, add it to the dataset. EX. ['Action', 'Adventure' 'Thriller]. This piece of data will be in all 3 datasets.
for genre in distinct_genres:
    genre_df = df[df['genres'].str.contains(genre, case=False, na=False)]
    filename = f'../data/{genre.replace(" ", "_").lower()}.csv'
    genre_df.to_csv(filename, index=False)


