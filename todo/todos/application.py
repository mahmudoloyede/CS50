import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///todos.db")


@app.route("/")
@login_required
def index():
    w = db.execute("SELECT * FROM todos WHERE user_id = :iden AND status='uncomplete'", iden=session["user_id"])
    x = db.execute("SELECT * FROM todos WHERE user_id = :iden AND status='complete'", iden=session["user_id"])
    return render_template("index.html", rows=w, rowss=x)

@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        return render_template("add.html")
    else:
        a = request.form.get("task")
        b = request.form.get("date_to")
        c = request.form.get("time_to")
        if ((not a) and (not b)) and (not c):
            return apology("please complete the form")
        db.execute("INSERT INTO todos (user_id, task, date, time, status, time_comp) VALUES(:iden, :task, :date, :time, :status, CURRENT_TIMESTAMP)", iden=session["user_id"], task=a, date=b, time=c, status='uncomplete')
        flash("Task added!")
        return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm-password")
        a = db.execute("SELECT * FROM users WHERE username= :name", name=username)
        if not username:
            return apology("You must provide a username", 403)
        elif len(a) != 0:
            return apology("This username already exists", 403)
        elif password != confirm:
            return apology("passwords do not match", 403)
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :h)", username=username, h=generate_password_hash(confirm))
        flash('Registered!')
    return redirect("/")


@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    if request.method == "GET":
        a = db.execute("SELECT * FROM todos WHERE user_id = :iden AND status='uncomplete'", iden=session["user_id"])
        return render_template("confirm.html", rows=a)
    else:
        b = request.form.get("task")
        db.execute("UPDATE todos SET status='complete', time_comp=CURRENT_TIMESTAMP WHERE task=:task AND user_id=:iden", task=b, iden=session["user_id"])
        flash("Task Confirmed!")
    return redirect("/")


@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == "GET":
        a = db.execute("SELECT * FROM todos WHERE user_id = :iden", iden=session["user_id"])
        return render_template("delete.html", rows=a)
    else:
        b = request.form.get("task")
        db.execute("DELETE FROM todos WHERE task=:task AND user_id = :iden", task=b, iden=session["user_id"])
        flash("Task Deleted!")
    return redirect("/")

@app.route("/change", methods=["POST", "GET"])
def change():
    if request.method == "GET":
        return render_template("change.html")
    else:
        a = request.form.get("password")
        b = request.form.get("new-password")
        c = request.form.get("confirm-password")
        d = db.execute("SELECT hash FROM users WHERE id=:iden", iden=session["user_id"])
        if not a:
            return apology("Please input old password")
        if not b:
            return apology('please insert a new password')
        if b != c:
            return apology("password do not match")
        if not check_password_hash(d[0]['hash'], a):
            return apology("old password does not match")
        db.execute("UPDATE users SET hash=:h WHERE id=:iden", h=generate_password_hash(b), iden=session['user_id'])
        flash('Password changed!')
        return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
