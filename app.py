""" Flask app """
import os
import dotenv

from helpers import login_required

from data_manager import alliance_place_stats, place_stats, perc_win, get_team_avg_qual_place

dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

from flask import Flask, session, render_template, redirect, request
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import datetime

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# From CS50 Finance
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/alliances/<year>")
def alliances(year):
    stuff = perc_win(year)
    print(stuff)
    return render_template("alliances.html", alliances=stuff)

@app.route("/team/<code>/avg_quals/<start>/<end>")
def quals_bounded(code, start, end):
    avg = get_team_avg_qual_place(code, int(start), int(end))
    print(avg)
    return render_template("quals.html", avg=avg)

@app.route("team/<code>")
def team(code):
    return