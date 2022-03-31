import collections
from functools import wraps
from operator import truediv
from pickle import FALSE, TRUE
from typing import Collection
from flask import Flask, render_template, request, redirect, flash, send_from_directory, url_for, session, logging, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt 
from flask_bootstrap import Bootstrap
from os import path


#1. Create a flask app which connects to MongoDB
app = Flask(__name__)
db = app.config["MONGO_URI"] = "mongodb://localhost:27017/wad"
app.config['SECRET_KEY']='thisisansecretkey'
mongo = PyMongo(app)
auth = HTTPBasicAuth()
bootstrap = Bootstrap(app)


#------------------------------AUTHENTICATION------------------------------------------#

@app.route("/") 
def default():
    return render_template("default.html")

def checkLogedinUser():
    if 'userlogedin' in session:
        return True
    else: return False

@app.route("/logout")
def logout():
    if 'userlogedin' in session:
        session.pop('userlogedin', None)
    return redirect(url_for('default'))


@app.route("/auth",methods=["GET", "POST"])
#@auth.login_required
def index():
    if request.method == "GET":
        return render_template("login.html", username="", password="")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        print(username)
        print(password)
        if mongo.db.users.find_one({"username": username, "password": password}):
            session["userlogedin"] = username
            return redirect(url_for('secret'))
        else:
            flash('This user is not registered yet. Please register the User first!', 'warning')
            
            return render_template("failed.html")


@app.route("/secret", methods=['GET', 'POST'])
def secret():
    if checkLogedinUser():
        return render_template("secret.html")
    else:
        flash ("Please log in first!", 'warning')
        return redirect(url_for("index"))


#-------------------------------SIGNUP----------------------------------------------------------#

     
@app.route("/signup",methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        if mongo.db.users.find_one({"username": username}):
            flash('Please choose another Username, this one is already taken!', 'warning')
            return render_template("signup.html")
        else:
            mongo.db.users.insert_one({
            'username': username,
            'password': password
            })
            flash('Registration was successfull! You can now log in!', 'success')
            return redirect(url_for('index'))




#--------------------------------------------PROFILE PAGE-------------------------------#

@app.route("/profile")
def profile():
    if checkLogedinUser():
        return render_template("cv.html")
    else:
        flash ("Please log in first!", 'warning')
        return redirect(url_for("index"))

    

@app.route("/blogposts")
def blogposts():
    notes = list(mongo.db.notes.find({}))
    return render_template("blogpublic.html", notes=notes)

#----------------------------- ADD BLOG COMMENT-------------------------------#

@app.route('/blog', methods=['GET', 'POST'])
def notebook():
    if checkLogedinUser():    
        # Render page on GET request
        if request.method == 'GET':
            # handle if user set limit number of notes to be displayed
            number = request.args.get('number')
            if number and int(number) > 0:
                notes = list(mongo.db.notes.find({}).limit(int(number)))
            
                # Send flash message
                flash(f"Limit applied. Show {len(notes)} notes")
        
                # Otherwise display all notes in database 
            else:
                notes = list(mongo.db.notes.find({}))
        
                # Render notebook page with existing notes
                return render_template('blog.html', notes=notes, number=len(notes))
    
        # Handle new note on POST request
        else:
            # Get title and content of the post
            title = request.form.get('title')
            content = request.form.get('note')

            # Save data to database
            mongo.db.notes.insert_one({
                'title': title,
                'content': content
            })

            # Flash message
            flash("New note added!")

             # Redirect user back to notebook page

            notes = list(mongo.db.notes.find({}))
    
            return render_template('blog.html', notes=notes)
    else:
        flash ("Please log in first!", 'warning')
        return redirect(url_for("index"))


#-------------------------PUBLIC BLOG PAGE------------------#

# Clear all notes features
@app.route('/blog/clear', methods=['POST'])
def clear_note():
    # Clear data in database
    mongo.db.notes.drop()

    # Redirect user back to notebook page
    return redirect('/blog')

#1.Runs at ‘http://localhost:5000’
if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)