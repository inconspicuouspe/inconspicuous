from os import environ
from json import loads
from traceback import format_exc
from secrets import token_urlsafe
from flask import (
    Flask,
    request,
    redirect,
    render_template,
    make_response,
    Request,
    jsonify,
    url_for,
    send_from_directory,
    Response
)
from user_agents import parse
from .database import MongoDB
from .authentication import login as auth_login
from .authentication import sign_up as auth_sign_up
from .authentication import logout as auth_logout
from .authentication import create_user_slot as auth_create_user_slot
from .authentication import disable_user as auth_disable_user
from .authentication import (
    extract_session,
    extract_session_or_empty,
    SESSION_DATA_COOKIE_NAME,
    Settings,
    username_constraints,
    remove_unfilled_user,
    set_permission_group,
    set_settings,
    add_csrf_token,
    verify_csrf_token
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
    FIELD_USER_ID,
    FIELD_CSRF_TOKEN,
    COOKIE_AGE
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
    response = make_response(render_template("home.html", exceptions=exceptions, session=session, Settings=Settings, consts=consts))
    if FIELD_CSRF_TOKEN not in request.cookies:
        return add_csrf_token(response)
    return response

@app.get("/control_panel/")
def control_panel():
    session = extract_session_or_empty(db, request)
    if not session:
        return redirect(url_for("home"))
    return render_template("controlPanel.html", exceptions=exceptions, session=session, Settings=Settings, consts=consts)

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
    response.set_cookie(SESSION_DATA_COOKIE_NAME, session_data.data, max_age=86400*30)
    return add_csrf_token(response)

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
    response.set_cookie(SESSION_DATA_COOKIE_NAME, session_data.data, max_age=COOKIE_AGE)
    return add_csrf_token(response)

@app.post("/logout/")
def logout():
    try:
        verify_csrf_token(request)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return auth_logout(db, jsonify({FIELD_SUCCESS: True}), request)

@app.post("/add_user/")
def add_user():
    form_data = request.json
    username = form_data[FIELD_USERNAME]
    permission_group = form_data[FIELD_PERMISSION_GROUP]
    settings = Settings(form_data[FIELD_SETTINGS])
    try:
        verify_csrf_token(request)
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
        verify_csrf_token(request)
        session = extract_session(db, request)
        if Settings._UNINVITE_MEMBERS not in session.settings:
            raise Unauthorized()
        remove_unfilled_user(db, username)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})

@app.post("/deactivate_user/")
def deactivate_user():
    form_data = request.json
    username = form_data[FIELD_USERNAME]
    try:
        verify_csrf_token(request)
        session = extract_session(db, request)
        if Settings._DISABLE_MEMBERS not in session.settings:
            raise Unauthorized()
        user_profile = db.get_user_profile(username)
        if user_profile.permission_group >= session.permission_group:
            raise Unauthorized()
        user_slot = auth_disable_user(db, username)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})

@app.get("/get_user_id/<username>/")
def get_user_id(username):
    try:
        session = extract_session(db, request)
        if Settings.VIEW_MEMBERS not in session.settings:
            raise Unauthorized()
        user_profile = db.get_user_profile(username)
        if user_profile.unfilled and Settings._RETRIEVE_INVITATION not in session.settings:
            raise Unauthorized()
        if user_profile.unfilled and (user_profile.permission_group >= session.permission_group or user_profile.settings not in session.settings):
            raise Unauthorized()
        user_id = user_profile.user_id
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True, FIELD_DATA: user_id})

@app.post("/edit_user_permission_group/")
def edit_user_permission_group():
    form_data = request.json
    username = form_data[FIELD_USERNAME]
    new_permission_group = form_data[FIELD_PERMISSION_GROUP]
    try:
        verify_csrf_token(request)
        session = extract_session(db, request)
        if Settings._EDIT_MEMBER_SETTINGS not in session.settings:
            raise Unauthorized()
        user_profile = db.get_user_profile(username)
        if user_profile.permission_group >= session.permission_group:
            raise Unauthorized()
        if new_permission_group >= session.permission_group:
            raise Unauthorized()
        set_permission_group(db, username, new_permission_group)
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})

@app.post("/edit_user_settings/")
def edit_user_settings():
    form_data = request.json
    username = form_data[FIELD_USERNAME]
    new_settings = form_data[FIELD_SETTINGS]
    try:
        verify_csrf_token(request)
        session = extract_session(db, request)
        if Settings._EDIT_MEMBER_SETTINGS not in session.settings:
            raise Unauthorized()
        user_profile = db.get_user_profile(username)
        if user_profile.permission_group >= session.permission_group:
            raise Unauthorized()
        set_settings(db, username, Settings(new_settings))
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True})

@app.get("/get_user/<username>/")
def get_user(username):
    try:
        session = extract_session(db, request)
        if Settings.VIEW_MEMBERS not in session.settings:
            raise Unauthorized()
        user_profile = db.get_user_profile(username)
        if user_profile.unfilled and Settings._VIEW_INVITED_MEMBERS not in session.settings:
            raise Unauthorized()
        if Settings._VIEW_MEMBER_SETTINGS not in session.settings or user_profile.permission_group > session.permission_group:
            permission_group = -1
            settings_value = -1
        else:
            permission_group = user_profile.permission_group
            settings_value = user_profile.settings.value
        user_id = user_profile.user_id if not user_profile.unfilled else "???"
    except MyError as exc:
        return jsonify({FIELD_SUCCESS: False, FIELD_REASON: exc.identifier})
    return jsonify({FIELD_SUCCESS: True, FIELD_DATA: {
        FIELD_USERNAME: user_profile.username,
        FIELD_SETTINGS: settings_value,
        FIELD_PERMISSION_GROUP: permission_group,
        FIELD_USER_ID: user_id
    }})

@app.get("/manifest/")
def get_manifest():
    return render_template("manifest.json")

@app.get("/github_oauth_callback/")
def github_oauth_callback():
    return ""