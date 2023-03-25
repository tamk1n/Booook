import os, json
from flask import Flask, redirect, render_template, request, session, flash, jsonify
from authentication import requires_auth, libs_nav
from flask_session import Session
import sqlite3
from password import checklength, checknumber, checkletter
from passlib.hash import pbkdf2_sha256
from flask_mail import Mail, Message
import requests
import datetime
from datetime import datetime

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tamkintamraz@gmail.com'
app.config['MAIL_PASSWORD'] = 'huoedvyjbxnxedaf'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)


@app.route("/")
def index():
    # Get method
    # Check user logged in
    if requires_auth():
        return redirect("/login")

    # add libraries of user to session
    session["libs"] = libs_nav()

    return render_template("index.html")

@app.route("/user")
def user():
    # Check user logged in
    if requires_auth():
        return redirect("/login")

    # get user's id from url
    user = request.args.get("id")

    # database connection start
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    # if user exists, all of information got from database
    if int(user) == session["user_id"]:
        user_info = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        print(user_info)
        wtr = db.execute("SELECT COUNT(book_id) FROM shelf WHERE lib_id IN (SELECT id FROM library WHERE user_id = ? AND name = 'Want to read')", (session["user_id"],)).fetchone()[0]
        read = db.execute("SELECT COUNT(book_id) FROM shelf WHERE lib_id IN (SELECT id FROM library WHERE user_id = ? AND name = 'Read')", (session["user_id"],)).fetchone()[0]
        cread = db.execute("SELECT COUNT(book_id) FROM shelf WHERE lib_id IN (SELECT id FROM library WHERE user_id = ? AND name = 'Currently reading')", (session["user_id"],)).fetchone()[0]
        rating = db.execute("SELECT COUNT(rating) FROM book WHERE user_id = ?", (session["user_id"],)).fetchone()[0]
        review = db.execute("SELECT COUNT(review) FROM comment WHERE user_id = ?", (session["user_id"],)).fetchone()[0]

        shelf = {
            "Want to read": wtr,
            "Currently reading": cread,
            "Read": read
        }
        print(read)
        print(cread)
        print(wtr)
        return render_template("user.html", user_info = user_info, shelf = shelf, rating = rating, review = review)
    else:
        flash("You do not have access", "danger")
        return redirect("/")


@app.route("/search")
def search():
    # Get method
    # Check user logged in
    if requires_auth():
        return redirect("/login")

    # option and search got from url
    selected_value = request.args.get("option")
    term = request.args.get("search")

    print(term)
    print(selected_value)

    if selected_value:
        url = f"https://www.googleapis.com/books/v1/volumes?q=search+{selected_value}{term}&maxResults=20"
    else:
        url = f"https://www.googleapis.com/books/v1/volumes?q=search+{term}&maxResults=20"

    # got response and convert to json
    response = requests.get(url)
    print(url)

    try:
        data = response.json()
        return render_template("search.html", data = data)
    except:
        flash("No available book based on your search", "danger")
        return redirect("/")

# Submit books to challenge
@app.route("/challenge", methods = ["POST", "GET"])
def challenge():
    #Auth
    if requires_auth():
        return redirect("/login")

    #database connection
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    # check for any challenge exist
    challenge = db.execute("SELECT * FROM challenge WHERE user_id = ?", (session["user_id"],)).fetchone()
    if challenge:
        # get book name from select via POST
        book_name = request.form.get("book")
        print(book_name)
        # details about challenge
        details = db.execute("SELECT end, number FROM challenge WHERE user_id = ?", (session["user_id"],)).fetchone()

        # if time is up challenge will be deleted
        current_time = datetime.now().strftime("%Y-%m-%d")
        print(current_time)

        if current_time == details[0]:
            db.execute("DELETE FROM challenge WHERE user_id = ?", session["user_id"])
        # formmatting date
        end_obj = datetime.strptime(details[0], "%Y-%m-%d")
        formatted_end = end_obj.strftime("%d %B, %Y")

        # select books which has been read and not submitted to challenge
        books = db.execute("SELECT book_id FROM shelf WHERE lib_id IN (SELECT id FROM library WHERE user_id = ? AND name = 'Read' AND challenged = 0)", (session["user_id"],)).fetchall()

        # get data and convert to JSON from API and Update database
        titles = []
        for book in books:
            url = f"https://www.googleapis.com/books/v1/volumes/{book[0]}"
            response = requests.get(url)
            data = response.json()
            if book_name == data["volumeInfo"]["title"]:
                print("here")
                id = book[0]
                print(id)
                db.execute("UPDATE shelf SET challenged = 1 WHERE lib_id = (SELECT id FROM library WHERE name = 'Read' AND user_id = ?) AND book_id = ?", (session["user_id"], id))
            else:
                titles.append(data["volumeInfo"]["title"])

        # submitted books to challenge
        submitted = db.execute("SELECT COUNT(book_id) FROM shelf WHERE challenged = 1 AND lib_id IN (SELECT id FROM library WHERE user_id = ?)", (session["user_id"],)).fetchone()[0]

        # commit and close database
        connection.commit()
        connection.close()

        return render_template("challenge.html", challenge = challenge, end = formatted_end, details = details, titles = titles, submitted = submitted)
    if request.method == "GET":
        return render_template("challenge.html")

@app.route("/challenged", methods = ["POST"])
def challenged():
    # check user logged in
    if requires_auth():
        return redirect("/login")

    # create database connection
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    # get challenge name from input and check if it exist
    name = request.form.get("name").strip()
    if not name:
        flash("Please enter the name", "danger")
        return redirect("/challenge")
    print(name)

    #get number, start and end date for challenge
    number = request.form.get("number").strip()
    start_date = request.form.get("start-date")
    end_date = request.form.get("end-date")
    now = datetime.now()
    fnow = now.strftime("%Y-%m-%d")
    # if number not exist, not a number, not positive
    # start and end date for challenge not exist or end date before start date
    if not number or not number.isdigit() or int(number) < 1 or not start_date or not end_date or end_date <= start_date or end_date <= fnow:
        flash("Invalid input", "danger")
        return redirect("/challenge")

    # update challenge table in database
    db.execute("INSERT INTO challenge (name, start, end, number, user_id) VALUES (?, ?, ?, ?, ?)", (name, start_date, end_date, number, session["user_id"]))
    connection.commit()
    connection.close()

    return redirect("/challenge")

@app.route("/book", methods=["POST", "GET"])
def book():
    # check user logged in
    if requires_auth():
        return redirect("/login")
    # id of book got from url or via post
    if request.method == "GET":
        book_id = request.args.get("id")
        print(f"book_id: {book_id}")
    if request.method == "POST":
        book_id = request.form.get("book_id")

    # url, convert to json
    url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    #print(url)
    response = requests.get(url)
    
    if response.status_code == 200:
        pass
    else:
        message = "No book found!"
        return render_template("error.html", message=message)

    data = response.json()
    # database connection
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    # get library if have any
    try:
        library = db.execute("SELECT name FROM library WHERE user_id = ? AND id IN (SELECT lib_id FROM shelf WHERE book_id = ?)", (session["user_id"], book_id)).fetchone()[0]
    except:
        library = None

    # get user's rating
    # get reviews
    # get average rating of book
    reviews = db.execute("SELECT username, date, review, comment.id FROM users, comment WHERE users.id = comment.user_id AND book_id = ?", (book_id,)).fetchall()
    #book_rating = db.execute("SELECT AVG(rating) FROM book WHERE book_id = ?", (book_id,)).fetchone()
    """print(book_rating)
    if book_rating[0]:
        book_rating = round(book_rating[0], 1)
    else:
        book_rating = 0"""

    # add user's libraries to session
    session["libs"] = libs_nav()

    # commit commands and close connection
    connection.commit()
    connection.close()

    return render_template("book.html", data = data, library = library, reviews = reviews, user = session["username"])

@app.route("/author")
def author():
    # check user logged in
    if requires_auth():
        return redirect("/login")

    # get author's name from url and convert to json
    author = request.args.get("name")
    url = f"https://www.googleapis.com/books/v1/volumes?q=inauthor:{author}&maxResults=20"
    print(url)
    response = requests.get(url)
    data = response.json()


    return render_template("search.html", data = data)

@app.route("/subject")
def subject():
    # check user logged in
    if requires_auth():
        return redirect("/login")
    # get subject from url and convert to json
    subject = request.args.get("name")
    url = f"https://www.googleapis.com/books/v1/volumes?q=subject:{subject}&maxResults=20"
    print(url)
    response = requests.get(url)
    data = response.json()

    return render_template("search.html", data = data)

@app.route("/updatebook", methods=["POST", "GET"])
def update_book():
    # check user logged in
    if requires_auth():
        return redirect("/login")
    # get reading and book_id
    data = json.loads(request.get_data())
    reading = data["reading"]
    book_id = data["book_id"]
    #reading = request.form.get("reading")
    #book_id = request.form.get("book_id")
    print(reading)
    print(book_id)

    # create database connection
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    # get id of library based on its name and user
    library = db.execute("SELECT id FROM library WHERE name=? AND user_id=?", (reading, session["user_id"]))

    result = library.fetchone()

    print(result)

    # get library name and its id based on specific book and user
    shelfs = db.execute("SELECT name, id FROM library WHERE user_id = ? AND id IN (SELECT lib_id FROM shelf WHERE book_id = ?)", (session["user_id"], book_id))

    print(f"Shelfs : {shelfs}") #7
    allshelfs = shelfs.fetchall()
    print(allshelfs) #8

    if allshelfs:
        for shelf in allshelfs:
            print(f" In loop?: {shelf}")
            if shelf[0] in ["Want to read", "Read", "Currently reading"]:
                print(shelf[0])
                db.execute("DELETE FROM shelf WHERE book_id = ? AND lib_id = ?", (book_id, shelf[1]))

    print("After allshelf") #9

    # add book to library
    if result is None and reading != "None":
        print("In none")
        db.execute("INSERT INTO library (name, user_id, date) VALUES (?, ?, strftime('%d %m, %Y', datetime('now')))", (reading, session["user_id"]))
        lib = db.execute("SELECT id FROM library WHERE name = ? AND user_id = ?", (reading, session["user_id"]))
        res = lib.fetchone()
        db.execute("INSERT INTO shelf (lib_id, book_id, date) VALUES (?, ?, strftime('%Y-%m-%d', datetime('now')))", (res[0], book_id))

        # commit commands and close database
        connection.commit()
        connection.close()
        return reading

    if reading == "None":
        connection.commit()
        connection.close()
        return reading

    db.execute("INSERT INTO shelf (lib_id, book_id, date) VALUES (?, ?, strftime('%Y-%m-%d', datetime('now')))", (result[0], book_id))

    # commit command and close database
    connection.commit()
    connection.close()
    return reading



@app.route("/updaterating", methods=["POST", "GET"])
def rating():
    # check user logged in
    if requires_auth():
        return redirect("/login")
    book_id = request.args.get('id')
    # create connection to database
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    if request.method == 'POST':
        # get user's rating and id of book
        #rating = request.form.get("rating")
        #book_id = request.form.get("book_id")
        data = json.loads(request.get_data())
        rating = data['rating']
        book_id = data['book_id']
        print(rating)
        print(book_id)

        # check if rating is none
        # check if book already rated/it must be changed
        # check if book not rated new data inserted
        books = db.execute("SELECT book_id, user_id FROM book WHERE book_id = ? AND user_id = ?", (book_id, session["user_id"])).fetchone()
        if rating == "none":
            db.execute("DELETE FROM book WHERE book_id = ? AND user_id = ?", (book_id, session["user_id"]))
        elif books:
            db.execute("UPDATE book SET rating = ? WHERE book_id = ? AND user_id = ?", (rating, book_id, session["user_id"]))
        else:
            db.execute("INSERT INTO book (user_id, book_id, rating) VALUES (?, ?, ?)", (session["user_id"], book_id, rating))
    rating = db.execute("SELECT rating FROM book WHERE book_id = ? AND user_id = ?", (book_id, session["user_id"])).fetchone()
    print(f"book_id: {book_id}")
    print(f"rating: {rating}")

    # average rating
    ave_rating = db.execute("SELECT AVG(rating) FROM book WHERE book_id = ?", (book_id,)).fetchone()[0]
    if ave_rating:
        ave_rating = round(ave_rating, 1)
    else:
        ave_rating = 0

    # commit changes and close database
    connection.commit()
    connection.close()

    return jsonify({"rating": rating, "ave_rating": ave_rating})

@app.route("/register", methods = ["POST", "GET"])
def register():
    session["user_id"] = None
    # Post method
    if request.method == "POST":

        # Connection to database
        connection = sqlite3.connect("/home/tamkin/Booook")

        db = connection.cursor()
        # Get and check first name
        fname = request.form.get("fname")
        if not fname:
            flash("Please enter first name!", "danger")
            return render_template("register.html")

        # Get and check last name
        lname = request.form.get("lname")
        if not lname:
            flash("Please enter last name!", "danger")
            return render_template("register.html")

        # Get and check username exist
        username = request.form.get("username").strip()

        user = db.execute("SELECT COUNT(username) FROM users WHERE username = ?", (username,))
        result = user.fetchone()[0]
        if not username:
            flash("Please enter username!", "danger")
            return render_template("register.html")
        elif result != 0:
            flash("Username already taken!", "danger")
            return render_template("register.html")

        # Get and check email exist
        email = request.form.get("email").strip()
        emailAdd = db.execute("SELECT COUNT(email) FROM users WHERE email = ?", (email,))
        if not email:
            flash("Please enter email address!", "danger")
            return render_template("register.html")
        elif emailAdd.fetchone()[0]:
            flash("This email address has already been registered!", "danger")
            return render_template("register.html")

        # Get check password
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or checklength(password) or checkletter(password) or checknumber(password) or confirmation != password: # if error -> returns true
            flash("No/Invalid password", "danger")
            return render_template("register.html")

        # Hash password
        hashed_password = pbkdf2_sha256.hash(password)

        # Insert new user to database
        db.execute("INSERT INTO users (firstname, lastname, username, email, hash) VALUES (?, ?, ?, ?, ?)", (fname, lname, username, email, hashed_password))

        # Add new user to session
        user_id = db.execute("SELECT id FROM users WHERE username = ?", (username, ))
        session["user_id"] = user_id.fetchone()[0]
        session["username"] = username

        # Commit changes and close connection to database
        connection.commit()
        connection.close()

        # Sending mail to user
        msg = Message(f'Congratulations, {username}', sender='tamkintamraz@gmail.com', recipients=[email])
        msg.body = "You are registered to Booook!"
        mail.send(msg)

        flash("You are registered!", "success")
        return redirect("/")

    if request.method == "GET":
        return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        # create database connection
        connection = sqlite3.connect("/home/tamkin/Booook")
        db = connection.cursor()

        # if any session clear
        session["user_id"] = None

        # get all information and check
        username = request.form.get("username")
        password = request.form.get("password").strip()
        if not username:
            flash("Please, enter username!", "danger")
            return render_template("login.html")
        if not password:
            flash("Please, enter password!", "danger")
            return render_template("login.html")
        try:
            user = db.execute("SELECT username, hash, id FROM users WHERE username = ?", (username.strip(),))
            result = user.fetchone()
        except:
            flash("Wrong username!", "danger")
            return render_template("login.html")
        
        if not result or not pbkdf2_sha256.verify(password.strip(), result[1]) or result[0] != username.strip():
            flash("Wrong username/password!", "danger")
            return render_template("login.html")

        # add info to session
        session["user_id"] = result[2]
        session["username"] = username

        # close connection
        connection.close()

        flash("You are logged in!", "success")
        return redirect("/")

    if request.method == "GET":
        session["user_id"] = None
        return render_template("login.html")

@app.route("/logout")
def logout():
    # check if user logged in
    if requires_auth():
        return redirect("/login")
    # if any session close
    if session["user_id"]:
        session.clear()
    flash("You are logged out!", "success")
    return redirect("/login")

@app.route("/library/<lib>")
def library(lib):
    # check user logged in
    if requires_auth():
        return redirect("/login")

    # create connection to database
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    # get books based on id of book and library and convert to JSON
    books = db.execute("SELECT book_id FROM shelf WHERE lib_id IN (SELECT id FROM library WHERE user_id = ? AND name = ?)", (session["user_id"], lib)).fetchall()
    count = len(books)
    detail = []
    for book in books:
        url = f"https://www.googleapis.com/books/v1/volumes/{book[0]}"
        response = requests.get(url)
        data = response.json()
        detail.append(data)

    # close connection to database
    connection.close()

    return render_template("library.html", detail = detail, lib = lib, count = count)

@app.route("/addreview", methods=["POST"])
def addreview():
    # check if user logged in
    if requires_auth():
        return redirect("/login")

    # get review, username and date
    data = json.loads(request.get_data())
    review = data['review']
    book_id = data['book_id']
    username = session["username"]
    date = datetime.now().strftime("%d.%m.%Y")

    print(f"Review for this book is {review}")

    # create connection to database
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    # check if user already reviewed the book
    check = db.execute("SELECT review FROM comment WHERE user_id = ? AND book_id = ?", (session["user_id"], book_id)).fetchone()
    if check:
        connection.commit()
        connection.close()
        return jsonify({"reviewed": True})
    

    # if not reviewed yet insert data to database
    db.execute("INSERT INTO comment (user_id, book_id, review, date) VALUES (?, ?, ?, ?)", (session["user_id"], book_id, review, date))

    id = db.execute("SELECT id FROM comment WHERE user_id = ?", (session["user_id"],)).fetchone()[0]

    connection.commit()

    connection.close()

    return jsonify({"username": username, 'review': review, "date": date, "id": id, "reviewed": False})

@app.route("/deletereview", methods=["GET", "POST"])
def deletereview():
    # check user logged in
    if requires_auth():
        return redirect("/login")
    # get comment id and delete from database
    #id = request.form.get("id")
    data = json.loads(request.get_data())
    id = data['id']
    print(f"id: {id}")
    book_id = data['book_id']
    print(id)
    connection = sqlite3.connect("/home/tamkin/Booook")
    db = connection.cursor()

    db.execute("DELETE FROM comment WHERE id = ?", (id, ))

    connection.commit()

    count = db.execute("SELECT COUNT(review) FROM comment WHERE book_id = ?", (book_id, )).fetchone()[0]
    connection.close()

    return jsonify({'count': count})
