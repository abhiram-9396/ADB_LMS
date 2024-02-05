from flask import Flask, flash, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from flask_paginate import Pagination
from bson.json_util import dumps

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'Abhiram'

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["LMS"]
    users = db.users
    print("Database Connection Established!!")
except:
    print("Unable to Connect to the Database!!")

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user_data = users.find_one({'email': email})

        if(user_data):
            email = user_data['email']
            # return f'{email} already exists!!'
            flash("Invalid: Email already exists.")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        user_data = {
            'email': email,
            'password': hashed_password
        }

        users.insert_one(user_data)

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user_data = users.find_one({'email': email})

        if(user_data == None):
            flash("User Data Not Found!! Try Signing Up!!!!")
            return render_template('login.html')

        if(not (check_password_hash(user_data['password'], password))):
            flash("Invalid: Wrong Password!")
            return render_template('login.html')

        if user_data and check_password_hash(user_data['password'], password):
            session['user'] = email
            return redirect(url_for('dashboard'))

    return render_template('login.html')

PER_PAGE = 2

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        books_collection = db.Books
        books = books_collection.find()
        
        page = int(request.args.get('page', 1))
        offset = (page - 1) * PER_PAGE
        paginated_books_cursor = books.skip(offset).limit(PER_PAGE)
        paginated_books = list(paginated_books_cursor)

        pagination = Pagination(page=page, total=books_collection.count_documents({}), per_page=PER_PAGE, css_framework='bootstrap4')

        message = f'Welcome, {session["user"]}! This is your dashboard.'
        user_data = users.find_one({'email': session['user']})

        return render_template('dashboard.html', books=paginated_books, message=message, user_data= user_data, pagination=pagination)
    else:
        return redirect(url_for('login'))

@app.route('/profile/<string:id>')
def profile(id):
    try:
        user_profile = users.find_one({"_id": ObjectId(id)})
        return render_template('profile.html', user_profile=user_profile)
    except:
        return "Error in fetching the user profile!!"


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
