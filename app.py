from flask import Flask, render_template, request, session, redirect, url_for
import requests
import pandas as pd
import os
from scripts.get_genres import get_genre_names

app = Flask(__name__)
app.secret_key = ""

@app.route('/')
def home():
    return render_template("home.html")
@app.route('/movie-questionnaire')
def index():
    genres = get_genre_names()
    return render_template("genre_selection.html", genres=genres)

# @app.route('/submit-genre', methods=['POST'])

@app.route('/liked-movies', methods=['GET', 'POST'])
def select_movies():
    if request.method == 'POST':
        shuffle = request.form.get('shuffle')
        selected_genres = request.form.getlist('genres')
        session['selected_genres'] = selected_genres
        azure_function_url = "http://localhost:7071/api/HttpTriggerGGSM"
        payload = {"genres": selected_genres}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(azure_function_url, json=payload, headers=headers)
        movie_data = {}
        if response.status_code == 200:
            movie_data = response.json()
            # print(movie_data['action'][0].get('title', 'No title found'))
            # print(movie_data)
            print("Genres sent successfully to Azure Function.")
            print("Genres being reshuffled:", selected_genres)

        
        else:
            print(f"Failed to send genres. Status code: {response.status_code}")

        return render_template("select-liked-movies.html", selected_genres=selected_genres, movie_data=movie_data)
    selected_genres = session.get('selected_genres', [])
    return render_template("select-liked-movies.html", selected_genres=selected_genres)

@app.route('/recommend-movies', methods=['GET', 'POST'])
def movie_recommendations():
    if request.method == 'POST':
        selected_movies = request.form.getlist('movies')
        print(f"Selected movies: {selected_movies}")
        azure_function_url_two = "http://localhost:7071/api/HttpTriggerMovieRecs"
        payload = {"movies": selected_movies}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(azure_function_url_two, json=payload, headers=headers)
        recommended_movies = {}
        if response.status_code == 200:
            recommended_movies = response.json()
            print(f"Selected movies sent successfully to Azure Function {azure_function_url_two}.")
        
        else:
            print(f"Failed to send selected movies. Status code: {response.status_code}")
            # Update this to handle multiple values for movie recommendation
        return render_template("movie-recommendations.html", recommended_movies=recommended_movies)
    return render_template("movie-recommendations.html")

if __name__ == '__main__':
    app.run(debug=True, port=5050)