from flask import Flask, request, redirect, render_template


app = Flask(__name__, template_folder="templates")

@app.get("/")
def home():
    return render_template("login.html")

@app.get("/login/")
def login():
    pass

@app.get("/register/")
def register():
    pass