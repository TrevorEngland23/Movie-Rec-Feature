from flask import Flask, render_template, request, session
import requests
import pandas as pd
import os
from scripts.get_genres import get_genre_names_and_image
import json

app = Flask(__name__)
app.secret_key = ""

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/movie-questionnaire')
def index():
    genres_and_images = get_genre_names_and_image()
    return render_template("genre_selection.html", genres=genres_and_images)

# @app.route('/submit-genre', methods=['POST'])

@app.route('/liked-movies', methods=['GET', 'POST'])
def select_movies():
    if request.method == 'POST':
        selected_genres = request.form.getlist('genres')
        # print(f"Selected Genres from user: {selected_genres}")
        session['selected_genres'] = selected_genres

        azure_function_url = "http://localhost:7071/api/HttpTriggerGGSM"
        payload = {"genres": selected_genres}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(azure_function_url, json=payload, headers=headers)
       
        movie_data = {}
        if response.status_code == 200:
            movie_data = response.json()
            session['movie_data'] = movie_data
            print("Genres sent successfully to Azure Function.")
            if request.form.get("shuffle") == "true":
                print("Genres being reshuffled:", selected_genres)

        
        else:
            print(f"Failed to send genres. Status code: {response.status_code}")

        return render_template("select-liked-movies.html", selected_genres=selected_genres, movie_data=movie_data)
    
    selected_genres = session.get('selected_genres', [])
    movie_data = session.get('movie_data', {})
    return render_template("select-liked-movies.html", selected_genres=selected_genres, movie_data=movie_data)

@app.route('/recommend-movies', methods=['GET', 'POST'])
def movie_recommendations():
    azure_function_url_two = 'http://localhost:7071/api/HttpTriggerMovieRecs'
    headers = {'Content-Type': 'application/json'}
    selected_genres = session.get('selected_genres', [])

    if request.method == 'POST':
        selected_movies = request.form.getlist('movies')
        
        print(f"Selected movies: {selected_movies}")
        session['selected_movies'] = selected_movies
    else:
       selected_movies = session.get('selected_movies', [])
    

    recommended_movies = {}
    genre_bar_chart = None
    genre_pie_chart = None
    cosine_similarity_chart = None

    if selected_movies:
        payload = {"movies": selected_movies, "genres": selected_genres}
        print(f"PAYLOAD: {payload}")
        try:
            response = requests.post(azure_function_url_two, json=payload, headers=headers)
            if response.status_code == 200:
                json_response = response.json()
                recommended_movies = json_response.get("recommended_movies", [])
                print(f"recommended movies: {recommended_movies}")
                genre_bar_chart = json_response.get("genre_bar_chart")
                genre_pie_chart = json_response.get("genre_pie_chart")
                cosine_similarity_chart = json_response.get("cosine_similarity_chart")
                print(f"Successfully re-triggered Azure Function")
            else:
                print(f"Azure Function failed with status {response.status_code}")
        except Exception as e:
            print(f"Error calling Azure Function: {e}")

    return render_template(
        "movie-recommendations.html",
        recommended_movies=recommended_movies,
        selected_movies=selected_movies,
        genre_bar_chart=genre_bar_chart,
        genre_pie_chart=genre_pie_chart,
        cosine_similarity_chart=cosine_similarity_chart
    )


if __name__ == '__main__':
    app.run(debug=True, port=5050)