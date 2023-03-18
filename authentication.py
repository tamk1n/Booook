from flask import session
import sqlite3

# check user logged in function
def requires_auth():
    if session.get("user_id") == None:
        return True
    return False

def libs_nav():
    connection = sqlite3.connect("booook.db")
    db = connection.cursor()
    libs = db.execute("SELECT name FROM library WHERE user_id = ?", (session["user_id"], )).fetchall()
    return libs