from flask import Flask, flash, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from flask_paginate import Pagination
from bson.json_util import dumps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('MY_SECRET_KEY')

try:
    client = MongoClient(os.getenv('MONGO_URL'))
    db = client["LMS"]
    users = db.users
    admins = db.admins
    print("Database Connection Established!!")
except:
    print("Unable to Connect to the Database!!")

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        studentID = request.form['studentID']

        user_data = users.find_one({'email': email})

        if(user_data):
            email = user_data['email']
            flash("Invalid: Email already exists.")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        user_data = {
            'email': email,
            'password': hashed_password,
            'name': name,
            'studentID': studentID,
            'role': "Student",
            'BookHistory':[]
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

@app.route('/adminLogin', methods=['GET','POST'])
def adminLogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admins_data = admins.find_one({'email': email})

        if(admins_data == None):
            flash("User Data Not Found!! Try Signing Up!!!!")
            return render_template('adminLogin.html')
        
        if(admins_data['role'] != "Admin"):
            flash("Role Must be Admin!!!!")
            return render_template('adminLogin.html')
        
        if(not (check_password_hash(admins_data['password'], password))):
            flash("Invalid: Wrong Password!")
            return render_template('adminLogin.html')

        if admins_data and check_password_hash(admins_data['password'], password):
            session['user'] = email
            return render_template('adminDashboard.html', admins_data = admins_data)
        
    return render_template('adminLogin.html')

PER_PAGE = 10


@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        books_collection = db.Books
        user_data = users.find_one({'email': session['user']})

        # Retrieve filter parameters from the query string
        isbn = request.args.get('isbn', '')
        title = request.args.get('title', '')
        author = request.args.get('author', '')
        branch = request.args.get('branch', '')
        genre = request.args.get('genre', '')

        # Build the query based on the filter criteria
        query = {
            'ISBN': {'$regex': f'.*{isbn}.*', '$options': 'i'},
            'Title': {'$regex': f'.*{title}.*', '$options': 'i'},
            'Author': {'$regex': f'.*{author}.*', '$options': 'i'},
            'Branch': {'$regex': f'.*{branch}.*', '$options': 'i'},
            'Genre': {'$regex': f'.*{genre}.*', '$options': 'i'}
        }

        # Pipeline for filtering and counting
        pipeline = [
            {'$match': query},
            {'$group': {'_id': None, 'count': {'$sum': 1}}}
        ]

        # Execute pipeline
        result = list(books_collection.aggregate(pipeline))

        # Retrieve count from the result
        total_filtered_books = result[0]['count'] if result else 0

        # Fetch filtered data from MongoDB
        page = int(request.args.get('page', 1))
        offset = (page - 1) * PER_PAGE
        paginated_books_cursor = books_collection.find(query).skip(offset).limit(PER_PAGE)
        paginated_books = list(paginated_books_cursor)

        pagination = Pagination(page=page, total=total_filtered_books, per_page=PER_PAGE, css_framework='bootstrap4')

        user_data = users.find_one({'email': session['user']})
        print(type(user_data))
        message = f'Welcome, {user_data["name"]}! This is your dashboard.'

        return render_template('dashboard.html', books=paginated_books, message=message, user_data=user_data, pagination=pagination) if pagination else render_template('dashboard.html', books=paginated_books, message=message, user_data=user_data)

    else:
        return redirect(url_for('login'))

@app.route('/bookRequest/<string:id>')
def bookRequest(id):
    try:
        user_profile = users.find_one({"_id": ObjectId(id)})
        return render_template('bookRequest.html', user_profile=user_profile)
    except:
        return "Error in fetching the user Book Request!!"

@app.route('/submitRequest/<string:id>', methods=['POST'])
def submitBookRequest(id):
    try:
        user_profile = users.find_one({"_id": ObjectId(id)})
        return user_profile
        
    except:
        return "Error in fetching the user Book Request!!"

@app.route('/profile/<string:id>')
def profile(id):
    try:
        user_profile = users.find_one({"_id": ObjectId(id)})
        return render_template('profile.html', user_profile=user_profile)
    except:
        return "Error in fetching the user profile!!"

@app.route('/addBook', methods=['GET','POST'])
def addBook():
    if request.method == 'POST':
        document = {
            'BookId': request.form['bookID'],
            'Title': request.form['title'],
            'Author': request.form['author'],
            'Genre': request.form['genre'],
            'ISBN': request.form['isbn'],
            'Branch': request.form['branch'],
            'Location': request.form['location'],
            'WaitingList': 0,
            'Availability': True
        }

        try:
            insert_result = db.Books.insert_one(document)
            if insert_result.acknowledged:
                flash("Book Added Successfully.")
                print("Book Added Successfully.")
            else:
                print("Failed to insert document.")
                flash("Invalid: Failed to insert document.")
        except Exception as e:
            print("Error:", str(e))
            return "Error occurred while adding the book: " + str(e)
        
    return render_template('adminDashboard.html')

@app.route('/deleteBook', methods=['GET','POST'])
def deleteBook():
    if request.method == 'POST':
        try:
            book_id = request.form['bookID']
            isbn = request.form['isbn']
            location = request.form['location']

            book = db.Books.find_one({'BookId': book_id, 'ISBN': isbn, 'Location': location})

            if book:
                db.Books.delete_one({'BookId': book_id, 'ISBN': isbn, 'Location': location})
                flash("Book deleted successfully.")
            else:
                return "No book found with provided BookId, ISBN, and Location."

        except Exception as e:
            print("Error:", str(e))
            return "Error occurred while deleting the book: " + str(e)

    return render_template('deleteBook.html')

@app.route('/editBook', methods=['GET','POST'])
def editBook():
    try:
        if request.method == 'POST':
            book_id = request.form['bookID']
            book = db.Books.find_one({'BookId': book_id})

            if book:
                book['Title'] = request.form['title']
                book['Author'] = request.form['author']
                book['Genre'] = request.form['genre']
                book['ISBN'] = request.form['isbn']
                book['Branch'] = request.form['branch']
                book['Location'] = request.form['location']

                db.Books.update_one({'BookId': book_id}, {'$set': book})
                flash("Book updated successfully.")
            else:
                return "Book with ID {} not found.".format(book_id)
    except Exception as e:
            print("Error:", str(e))
            return "Error occurred while editing the book: " + str(e)
    
    return render_template('editBook.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
