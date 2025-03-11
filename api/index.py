from flask import Flask, request, redirect, render_template, make_response, Request, jsonify
from user_agents import parse
from os import environ
from json import loads
from .database import MongoDB
from .authentication import login as db_login
from .authentication import modify_response

MONGO_DB_CONNECTION_URI = environ["MONGO_DB_CONNECTION_URI"]
MONGO_DB_PASSWORD = environ["MONGO_DB_PASSWORD"]
MONGO_DB_USERNAME = environ["MONGO_DB_USERNAME"]

db = MongoDB(MONGO_DB_CONNECTION_URI, MONGO_DB_USERNAME, MONGO_DB_PASSWORD)

app = Flask(__name__, template_folder="templates")

def session_name(__request: Request) -> str:
    parsed_user_agent = parse(__request.user_agent.string)
    browser = parsed_user_agent.browser.family
    os = parsed_user_agent.os.family
    return f"{browser} on {os}"

@app.get("/")
def home():
    return render_template("login.html")

@app.post("/login/")
def login():
    login_data = loads(request.data)
    username = login_data["username"]
    password = login_data["password"]
    session_data = db_login(db, username, password, session_name(request))
    if not session_data:
        return jsonify({"success": False})
    response = jsonify({"success": True})
    response.set_cookie("session_data", session_data.data)
    return response

@app.get("/register/")
def register():
    return render_template("login.html")
