import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import requests
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_file, Response
from flask_session import Session
from tempfile import mkdtemp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import faulthandler
import numpy as np
from io import StringIO, BytesIO
faulthandler.enable()

# configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 1
Session(app)

# ensure templates are auto-reloaded
app.config['TEMPLATES_AUTO_RELOAD'] = True

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    return response

db = "mymusic.db"

client_credentials_manager = SpotifyClientCredentials(client_id='20580f81b3734588b23c40e35a071d49',
                                                      client_secret='e139583585fe42efa972991cd8ab2287')

spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


@app.route("/")
def index():
    """ Main Page """ 

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ User Login """

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":
        if not request.form.get("username") or not request.form.get("password"):
            return render_template("error.html")

        # store form information into variables
        username = request.form.get("username")
        password = (request.form.get("password"))

        conn = sqlite3.connect(db)
        c = conn.cursor()

        # search database for username
        username_check = c.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        # check if user exists
        if username_check == None:
            return render_template("error.html")

        # generate credentials
        user_credentials = [str(item) for item in username_check]

        # check password hash
        if check_password_hash(user_credentials[2], password):
            session["user_id"] = user_credentials[1]
            return redirect("/")
        else:
            return render_template("error.html")

        return render_template("login.html", username_check=username_check)

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ User Registration """

    # Forget any user id
    session.clear()

    # User reached route via POST 
    if request.method == "POST":

        # check for valid forms    
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return render_template("error.html")

        # save form data to variables
        new_username = request.form.get("username")
        new_pw = request.form.get("password")
        new_pwconf = request.form.get("confirmation")

        # check if passwords match and hash it
        if new_pw == new_pwconf:
            hash_password = generate_password_hash(new_pw)
        else:
            return render_template("error.html")

        # check for existing user id / insert into user table
        conn = sqlite3.connect(db)
        c = conn.cursor()

        # check if existing username exists in db
        username_check = c.execute("SELECT username FROM users WHERE username = ?", (new_username,)).fetchone()
        if username_check == None:
            c.execute("INSERT INTO users(username, hashpw) VALUES (?, ?)", (new_username, hash_password))
        else:
            conn.close()
            return render_template("error.html")

        # commit changes to db and close
        conn.commit()
        conn.close()

        return redirect("/")
    else:
        return render_template("register.html")

    return render_template("register.html")


# Search for arist information
@app.route("/search", methods=["GET", "POST"])
def search():
    """ Search Artist Name and get top 10 tracks in US"""

    session.clear()

    if request.method == "POST":
        if not request.form.get("artist"):
            return render_template("search.html")
        
        # get user searched artist
        artist = request.form.get("artist")

        session["artist"] = artist

        # search and parse through artist data
        artist_search = spotify.search(q=artist, limit=1, offset=0 ,type="artist")
        artist_url = artist_search['artists']['items'][0]['external_urls']['spotify']
        artist_img = artist_search['artists']['items'][0]['images'][0]['url']
        artist_genre = artist_search['artists']['items'][0]['genres']

        # get artist top tracks
        artist_toptracks = spotify.artist_top_tracks(artist_url, country="US")

        # iterate over top 10 tracks and store name, uri and popularity
        artist_tracks = []
        for track in artist_toptracks['tracks']:
            artist_tracks.append([track['name'], track['uri'], track['popularity']])

        session['artist_tracks'] = artist_tracks

        # store artist features as dictionary of dictionaries
        toptracks_features = {}

        # get audio features for each track
        for track in artist_tracks:
            track_name = track[0]

            toptracks_features[track_name] = {}
            audiofeatures = spotify.audio_features(track[1])

            for features in audiofeatures[0]:
                if features == 'type':
                    break
                toptracks_features[track_name].update({features: audiofeatures[0][features]})

        session['toptracks_features'] = toptracks_features

        return render_template("images.html")

    else:
        return render_template("search.html")

    return render_template("search.html")


@app.route("/images")
def images():
    return render_template("images.html")


@app.route("/generate_fig")
def generate_fig():
    """ Generate matplot lib figure and send """
     
    artist_tracks = session.get('artist_tracks')
    artist = session.get('artist').upper()

    popularity = []
    song_name = []

    # separate track name and popularity score
    for track in artist_tracks:
        song_name.append(track[0])
        popularity.append(track[2])

    fig_size = plt.rcParams["figure.figsize"]
    fig_size[0] = 10
    fig_size[1] = 8
    plt.rcParams["figure.figsize"] = fig_size

    plt.title(artist + "'s Top 10 Songs Popularity Score")
    plt.plot(popularity, 'bo-')
    plt.yticks(np.arange(min(popularity), max(popularity)+1 , 1.0))
    plt.xticks(range(10), song_name, rotation=30, horizontalalignment="right")
    plt.tight_layout()

    # store image into memory
    img = BytesIO()
    plt.savefig(img, transparent=True)
    img.seek(0)
    plt.clf()
    plt.close('all')

    return send_file(img, mimetype="image/png")


# UNUSED
@app.route("/albums", methods=["GET"])
def albums():

    name = "{Seven Lions}" # chosen artist
    name_search = spotify.search(q=name, type='artist') # search for artist 
    name_url = name_search['artists']['items'][0]['external_urls']['spotify'] # extract artist url
    results = spotify.artist_top_tracks(name_url, country="US") # search for artist top tracks 

    top_tracks = []
    for track in results['tracks']:
        top_tracks.append([track['name'], track['uri'], track['popularity']])
    
    audio = spotify.audio_features(tracks=top_tracks[0][1])

    audios = {}
    for features in audio[0]:
        if features == 'type':
            break
        if features not in audios:
            audios[features] = audio[0][features]
    del audios['mode']

    return render_template("albums.html", name_search=name_search, name_url=name_url, top_tracks=top_tracks, audio=audios)


@app.route("/features", methods=["GET", "POST"])
def features():
    """ Plot user requested audio features """

    toptracks_features = session.get('toptracks_features')

    if request.method == 'POST':

        user_features = request.form.getlist("feature")

        tracks_featuresrequested = {}

        # create line of user feature
        for want in user_features:
            new_line = []
            for track in toptracks_features: 
                for feature in toptracks_features[track]: 
                    if want == feature:
                        new_line.append(toptracks_features[track][feature])
                        tracks_featuresrequested[feature] = new_line

        session['user_requesteddata'] = tracks_featuresrequested

        return render_template("image.html", featurereq=tracks_featuresrequested)

    else:
        return render_template("index.html")

    return render_template("images.html")


@app.route("/plot_userfeatures")
def plot_userfeatures():
    """ Plot user requested features """
    
    user_requested_features = session.get('user_requesteddata')
    artist_tracks = session.get('artist_tracks')
    artist = session.get("artist").upper()

    song_name = []

    for track in artist_tracks:
        song_name.append(track[0])

    fig_size = plt.rcParams["figure.figsize"]
    fig_size[0] = 10
    fig_size[1] = 8
    plt.rcParams["figure.figsize"] = fig_size
    

    for feature in user_requested_features:
        plt.plot(user_requested_features[feature], label=feature)

    plt.title(artist + "'s Top 10 Songs Audio Features")
    plt.legend(loc="upper left", framealpha=0.5)
    plt.xticks(range(10), song_name, rotation=30, horizontalalignment="right")
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, transparent=True)
    img.seek(0)
    plt.clf()
    plt.close('all')

    return send_file(img, mimetype="image/png")


@app.route("/audio")
def generate_audio():

    artist_tracks = session.get('artist_tracks')

    audio_features = {}
    audio_data = []
    audio_dict = {}

    # get audio features for each track
    for track in artist_tracks:
        track_name = track[0]

        # make song names as key values
        audio_features[track_name] = []
        audio_dict[track_name] = {}

        # get audio features
        audio = spotify.audio_features(track[1])

        # store audio features inside dictionary as list
        for features in audio[0]:
            if features == 'type':
                break
            audio_features[track_name].append([features, audio[0][features]])

            audio_dict[track_name].update({features: audio[0][features]})

    session['audio_dict'] = audio_dict

    return send_file(img, mimetype="image/png")
    