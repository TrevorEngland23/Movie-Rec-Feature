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

@app.route('/genre-selection')
def genre_selection():
    return "This is the genre selection page."

@app.route('/liked-movies')
def select_movies():
    return "Select your movies from this list"

@app.route('/recommend-movies')
def movie_recommendations():
    return "These are 10 movies you should check out"

if __name__ == '__main__':
    app.run(debug=True, port=5050)