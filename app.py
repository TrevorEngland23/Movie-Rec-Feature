from flask import Flask, render_template, request
import requests
import pandas as pd
import os
from scripts.get_genres import get_genre_names

app = Flask(__name__)

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
        selected_genres = request.form.getlist('genres')
        azure_function_url = "http://localhost:7071/api/HttpTriggerGGSM"
        payload = {"genres": selected_genres}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(azure_function_url, json=payload, headers=headers)
        movie_titles = {}
        if response.status_code == 200:
            movie_titles = response.json()
            print("Genres sent successfully to Azure Function.")
        
        else:
            print(f"Failed to send genres. Status code: {response.status_code}")
        return render_template("select-liked-movies.html", selected_genres=selected_genres, movie_titles=movie_titles)
    return render_template("select-liked-movies.html")

@app.route('/recommend-movies')
def movie_recommendations():
    return "These are 10 movies you should check out"

if __name__ == '__main__':
    app.run(debug=True, port=5050)