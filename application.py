import os

from flask import Flask, session, render_template, request, redirect, jsonify, json
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import psycopg2
import requests
from os import environ
import csv

app = Flask(__name__)

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL")) # database engine object from SQLAlchemy that manages connections to the database
                                                  # DATABASE_URL is an environment variable that indicates where the database lives
db = scoped_session(sessionmaker(bind=engine)) # create a 'scoped session' that ensures different users' interactions with the database are kept separate

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


Session(app)


# Set up database

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/success", methods=["GET","POST"])
def success():
    name = request.form.get("name")
    uname = request.form.get("uname")
    pwd = request.form.get("pwd")
    if db.execute("SELECT username FROM users WHERE username=:un", {"un": uname}).rowcount == 0:
        db.execute("INSERT INTO users (name, username, password) VALUES (:nm, :un, :pw)",
                  {"nm": name, "un": uname, "pw": pwd})
        db.commit()
        return render_template("success.html", Name=name)
    else:
        return render_template("error.html", message="User-name already taken. Please try another one.")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/home", methods=["GET","POST"])
def home():
    liu=request.form.get("u")
    lp=request.form.get("P")
    if request.method=="POST":
        if db.execute("SELECT * FROM users WHERE username=:liu AND password=:lp", {"liu":liu, "lp":lp} ).rowcount == 0:
            alert=1
            return render_template("login.html",alert=alert)
        else:
            session["user_name"] =liu
            return render_template("home.html")
    else:
        return render_template("home.html")        

@app.route("/sresults", methods=["POST","GET"])
def sresults():
    return render_template("results.html", title = get_title())
def get_title():
    selres=request.form.get("select")
    ser='%'+request.form.get("search")+'%'
    if selres=="1":
        res=db.execute("SELECT * FROM books WHERE isbn LIKE :query",{"query":ser}).fetchall()
    elif selres=="2":
        res=db.execute("SELECT * FROM books WHERE title LIKE :query",{"query":ser}).fetchall()
    elif selres=="3":
        res=db.execute("SELECT * FROM books WHERE author LIKE :query",{"query":ser}).fetchall()
    return res

@app.route("/bookinfo/<string:tl>")
@app.route("/bookinfo/<string:tl>/<string:i1>")
@app.route("/bookinfo/<string:tl>/<string:i1>/<string:a>")
@app.route("/bookinfo/<string:tl>/<string:i1>/<string:a>/<string:y>")
@app.route("/bookinfo/<string:tl>/<string:i1>/<string:a>/<string:y>/<int:rc>")
def bookinfo(i1,tl,a,y):
    res=requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "vczLXQOlPgyPrtG18j3mSw", "isbns": i1})
    r=res.json()
    data=r["books"]
    ar=data[0]["average_rating"]
    wrc=data[0]["work_ratings_count"]
    if db.execute("SELECT * FROM reviews WHERE isbn=:i1",{"i1":i1}).rowcount!=0:
        revs=db.execute("SELECT * FROM reviews WHERE isbn=:i1",{"i1":i1}).fetchall()
        return render_template("binfo.html",tl =tl,i1=i1,a=a,y=y,ar=ar,wrc=wrc,revs=revs)
    else:
        alert=1
        return render_template("binfo.html",tl =tl,i1=i1,a=a,y=y,ar=ar,wrc=wrc,alert=alert)
@app.route("/posted",methods=["GET","POST"])
def posted():
    i=request.form.get("isbn")
    u=request.form.get("username")
    rate=request.form.get("rating")
    op=request.form.get("opinion")
    if db.execute("SELECT username FROM users WHERE username= :un",{"un" : u}).rowcount==0:
        return render_template("error.html",message=i)
    else:
        if db.execute("SELECT * FROM reviews WHERE username= :un AND isbn= :i1",{"un": u,"i1":i}).rowcount!=0 :
            return render_template("error.html",message="Already posted a review. You cannot post a review for a book twice.")
        else:
            db.execute("INSERT INTO reviews (username, isbn, rating, comments) VALUES (:username, :isbn, :rate, :opinion)",{"username":u, "isbn": i, "rate": rate, "opinion": op})
            db.commit()
        return render_template("home.html",alert=1)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/api/books/<string:isbn>")
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn=:i",{"i":isbn}).fetchone()
    review = db.execute("SELECT * FROM reviews WHERE isbn=:i",{"i":isbn}).rowcount
    rating= db.execute("SELECT rating FROM reviews WHERE isbn=:i",{"i":isbn}).fetchall()
    rc= db.execute("SELECT rating FROM reviews WHERE isbn=:i",{"i":isbn}).rowcount
    sum=0
    for r in range(rc):
        sum=sum+rating[r]
    if sum==0 or rc==0:
        avg=0
    else:
        avg=sum/rc
    b="Hi"
    if book is None:
        return jsonify({"error": "Invalid isbn"}),422
    else:
         return jsonify({
         "title":book.title,
         "isbn":book.isbn,
         "author":book.author,
         "year":book.year,
         "ratings count":review,
         "average rating":avg
         })
