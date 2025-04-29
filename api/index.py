from os import environ
from json import loads
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
from .database import MongoDB
from .authentication import login as auth_login
from .authentication import sign_up as auth_sign_up
from .authentication import logout as auth_logout
from .authentication import create_user_slot as auth_create_user_slot
from .authentication import (
    extract_session,
    extract_session_or_empty,
    SESSION_DATA_COOKIE_NAME,
    Settings,
    username_constraints,
    remove_unfilled_user
)
from .exceptions import (
    MyError,
    Unauthorized,
    Unimplemented
)
from . import exceptions, consts
from .consts import (
    FIELD_SETTINGS,
    FIELD_USER_SLOT,
    FIELD_USERNAME,
    FIELD_PERMISSION_GROUP,
    FIELD_PASSWORD,
    FIELD_SUCCESS,
    FIELD_REASON,
    FIELD_DATA,
    FIELD_USER_ID
)

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
    return render_template("home.html", exceptions=exceptions, session=session, Settings=Settings, consts=consts)

@app.post("/login/")
def login():
    login_data = request.json
    username = login_data[FIELD_USERNAME]
    password = login_data[FIELD_PASSWORD]
    try:
        session_data = auth_login(db, username, password, session_name(request))
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    response = jsonify({FIELD_SUCCESS: True})
    response.set_cookie(SESSION_DATA_COOKIE_NAME, session_data.data)
    return response

@app.get("/register/")
def registration():
    return render_template("register.html", exceptions=exceptions, consts=consts)

@app.post("/register/")
def register():
    login_data = request.json
    username = login_data[FIELD_USERNAME]
    password = login_data[FIELD_PASSWORD]
    user_slot = login_data[FIELD_USER_SLOT]
    try:
        session_data = auth_sign_up(db, username, password, session_name(request), user_slot)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    response = jsonify({FIELD_SUCCESS: True})
    response.set_cookie(SESSION_DATA_COOKIE_NAME, session_data.data)
    return response

@app.post("/logout/")
def logout():
    return auth_logout(db, jsonify({FIELD_SUCCESS: True}), request)

@app.post("/add_user/")
def add_user():
    form_data = request.json
    username = form_data[FIELD_USERNAME]
    permission_group = form_data[FIELD_PERMISSION_GROUP]
    settings = Settings(form_data[FIELD_SETTINGS])
    try:
        session = extract_session(db, request)
        if Settings._CREATE_MEMBERS not in session.settings:
            raise Unauthorized()
        if settings not in session.settings:
            raise Unauthorized()
        if permission_group >= session.permission_group:
            raise Unauthorized()
        if username.startswith("TEST_USERNAME_USING_THIS_NAME_WILL_NOT_CREATE_A_USER"):
            user_slot = "NO_USER_SLOT_GENERATED"
        else:
            username_constraints(username)
            user_slot = auth_create_user_slot(db, settings, permission_group, username)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True, FIELD_DATA: user_slot})

@app.get("/user_list/")
def get_user_list():
    try:
        session = extract_session(db, request)
        if Settings.VIEW_MEMBERS not in session.settings:
            raise Unauthorized()
        view_member_settings = Settings._VIEW_MEMBER_SETTINGS in session.settings
        view_invited_members = Settings._VIEW_INVITED_MEMBERS in session.settings
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    users = [
        {
            FIELD_USERNAME: user.username,
            FIELD_SETTINGS: user.settings.value if view_member_settings and user.permission_group <= session.permission_group else -1,
            FIELD_PERMISSION_GROUP: user.permission_group if view_member_settings and user.permission_group <= session.permission_group else -1,
            FIELD_USER_ID: user.user_id if not user.unfilled else "???"
        }
        for user in db.list_users()
        if not user.unfilled or view_invited_members
    ]
    return jsonify({FIELD_SUCCESS: True, FIELD_DATA: users})

@app.post("/remove_user/")
def remove_user():
    form_data = request.json
    username = form_data[FIELD_USERNAME]
    try:
        session = extract_session(db, request)
        if Settings._UNINVITE_MEMBERS not in session.settings:
            raise Unauthorized()
        remove_unfilled_user(db, username)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})

@app.post("/deactivate_user/")
def deactivate_user():
    try:
        raise Unimplemented()
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})

@app.post("/edit_user_permission_group/")
def edit_user_permission_group():
    try:
        raise Unimplemented()
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})

@app.post("/edit_user_settings/")
def edit_user_settings():
    try:
        raise Unimplemented()
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})