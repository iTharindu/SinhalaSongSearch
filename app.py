from elasticsearch import Elasticsearch, helpers
import json
from flask import Flask
from wtforms import Form, StringField, SelectField
from flask import flash, render_template, request, redirect, jsonify
import re
from googletrans import Translator
from search import search_query_filtered, search_query

es = Elasticsearch([{'host': 'localhost', 'port':9200}])
app = Flask(__name__)


global_search = "dada"
global_artists = []
global_genre = []
global_music = []
global_lyrics = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global global_search
    global global_artists
    global global_genre
    global global_music
    global global_lyrics
    if request.method == 'POST':
        if 'form_1' in request.form:
            if request.form['nm']:
                search = request.form['nm']
                global_search = search
                print(global_search)
            else :
                search = global_search
            list_songs, artists, genres, music, lyrics = search_query(search)
            global_artists, global_genre, global_music, global_lyrics = artists, genres, music, lyrics
        elif 'form_2' in request.form:
            search = global_search
            artist_filter = []
            genre_filter = []
            music_filter = []
            lyrics_filter = []
            for i in global_artists :
                if request.form.get(i["key"]):
                    artist_filter.append(i["key"])
            for i in global_genre :
                if request.form.get(i["key"]):
                    genre_filter.append(i["key"])
            for i in global_music:
                if request.form.get(i["key"]):
                    music_filter.append(i["key"])
            for i in global_lyrics:
                if request.form.get(i["key"]):
                    lyrics_filter.append(i["key"])
            list_songs, artists, genres, music, lyrics = search_query_filtered(search, artist_filter, genre_filter, music_filter, lyrics_filter)
        return render_template('index.html', songs = list_songs, artists = artists, genres = genres, music = music, lyrics = lyrics)
    return render_template('index.html', songs = '', artists = '',  genres = '', music = '', lyrics = '')

if __name__ == "__main__":
    app.run(debug=True)
