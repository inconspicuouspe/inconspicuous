from os import environ
from json import loads
from .database import MongoDB
from .authentication import login as auth_login
from .authentication import extract_session, extract_session_or_empty
from .authentication import sign_up as auth_sign_up
from .exceptions import (
    MyError
)
from . import exceptions
from flask import (
    Flask,
    request,
    redirect,
    render_template,
    make_response,
    Request,
    jsonify,
    url_for
)
from user_agents import parse

FIELD_REASON = "reason"
FIELD_SUCCESS = "success"

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
    session = extract_session_or_empty(db, request)
    return render_template("home.html", exceptions=exceptions, session=session)

@app.post("/login/")
def login():
    login_data = request.json
    username = login_data["username"]
    password = login_data["password"]
    try:
        session_data = auth_login(db, username, password, session_name(request))
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    response = jsonify({FIELD_SUCCESS: True})
    response.set_cookie("session_data", session_data.data)
    return response

@app.get("/register/")
def registration():
    return render_template("register.html", exceptions=exceptions)

@app.post("/register/")
def register():
    login_data = request.json
    username = login_data["username"]
    password = login_data["password"]
    user_slot = login_data["user_slot"]
    try:
        session_data = auth_sign_up(db, username, password, session_name(request), user_slot)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})