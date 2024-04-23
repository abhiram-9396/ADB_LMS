from flask import Flask, flash, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from flask_paginate import Pagination
from bson.json_util import dumps
import os
from dotenv import load_dotenv
from datetime import date, timedelta, datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# Routes for Student

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
            'due_amount': 0
        }

        users.insert_one(user_data)
        flash("SignUp Completed Successfully!!")

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

PER_PAGE = 10

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        copy_collection = db.Copies
        user_data = users.find_one({'email': session['user']})

        # Retrieve filter parameters from the query string
        isbn = request.args.get('isbn', '')
        title = request.args.get('title', '')
        author = request.args.get('author', '')
        genre = request.args.get('genre', '')

        # Build the query based on the filter criteria
        query = {
            'ISBN': {'$regex': f'.*{isbn}.*', '$options': 'i'},
            'Title': {'$regex': f'.*{title}.*', '$options': 'i'},
            'Author': {'$regex': f'.*{author}.*', '$options': 'i'},
            'Genre': {'$regex': f'.*{genre}.*', '$options': 'i'}
        }

        # Pipeline for filtering and counting
        pipeline = [
            {'$match': query},
            {'$group': {'_id': None, 'count': {'$sum': 1}}}
        ]

        # Execute pipeline
        result = list(copy_collection.aggregate(pipeline))

        # Retrieve count from the result
        total_filtered_books = result[0]['count'] if result else 0

        # Fetch filtered data from MongoDB
        page = int(request.args.get('page', 1))
        offset = (page - 1) * PER_PAGE
        paginated_books_cursor = copy_collection.find(query).skip(offset).limit(PER_PAGE)
        paginated_books = list(paginated_books_cursor)

        pagination = Pagination(page=page, total=total_filtered_books, per_page=PER_PAGE, css_framework='bootstrap4')

        user_data = users.find_one({'email': session['user']})
        print(type(user_data))
        message = f'Welcome, {user_data["name"]}! This is your dashboard.'

        return render_template('dashboard.html', copies=paginated_books, message=message, user_data=user_data, pagination=pagination) if pagination else render_template('dashboard.html', copies=paginated_books, message=message, user_data=user_data)

    else:
        return redirect(url_for('home'))

@app.route('/Copy/<string:CopyId>', methods=['GET','POST'])
def CopyDetails(CopyId):
    if 'user' in session:
        copy_details = db.Copies.find_one({"CopyId": CopyId})
        copy_location = db.CopyLocation.find_one({"CopyId": CopyId})
        return render_template('copyDetails.html', Details=copy_details, Location=copy_location )
    else:
        return redirect(url_for('home'))

@app.route('/bookRequest/<string:id>', methods=['GET','POST'])
def bookRequest(id):
    if 'user' in session:
        user_profile = users.find_one({"_id": ObjectId(id)})
        return render_template('bookRequest.html', user_profile=user_profile)
    else:
        return redirect(url_for('home'))

@app.route('/bookRenew/<string:id>')
def bookRenew(id):
    if 'user' in session:
        try:
            user_profile = users.find_one({"_id": ObjectId(id)})
            return render_template('renewBook.html', user_profile=user_profile)
        except:
            return "Error in fetching the user Book Request!!"
    else:
        return redirect(url_for('home'))

@app.route('/submitRequest', methods=['POST'])
def submitBookRequest():
    if 'user' in session:
        if request.method == 'POST':
            try:
                # StudentID = request.form['studentID']
                bookId = request.form['bookID']
                reservation_exist = db.Reservation.find_one({'CopyId': bookId})
                book_available = db.Copies.find_one({'CopyId': bookId})
                copyloc = db.CopyLocation.find_one({'CopyId': bookId})
                # user = db.users.find_one({"studentID": StudentID})
                if book_available['Availability'] == False and reservation_exist:
                    # send_email("abhiramgat@gmail.com", "abhiram@gat12", email, "LMS Book Request", msg )
                    return "The Requested Book Will Be Expected To Be Available On {}".format(reservation_exist['ExpectedDate'])
                elif book_available['Availability'] == True:
                    return "Your Requested Book Is Available at {} Location!!".format(copyloc['Location'])
                else:
                    return "Your response is recorded!!"

            except Exception as e:
                return "Error in fetching the user Book Request!!" + str(e)
    else:
        return redirect(url_for('home'))

@app.route('/bookRenewRequest/<string:StudentId>', methods=['POST'])
def bookRenewRequest(StudentId):
    if 'user' in session:
        try:
            CopyId = request.form['bookID']
            transaction_exist = db.Transaction.find_one({'StudentID': StudentId, 'Type': "CheckOut"})
            transaction_exist_checkedin = db.Transaction.find_one({'StudentID': StudentId, 'Type': "CheckIn"})
            
            if transaction_exist_checkedin:
                for doc in transaction_exist_checkedin['CopyList']:
                    if doc['CopyId'] == CopyId:
                        return "Book Is Already Checked IN..Renewal Not Possible!"
                    else:
                        return "This Book Is Not Checked Out By You!!"
                    
            if transaction_exist:
                for doc in transaction_exist['CopyList']:
                    if doc['CopyId'] == CopyId:
                        print("transaction_exist is : ", transaction_exist)
                        #-----renewing the request------
                        if doc['RenewCount'] > 0:
                            doc['RenewCount'] -= 1
                            doc["ExpiresOn"] = str(date.today() + timedelta(days=30))
                            db.Transaction.update_one({'StudentID': StudentId, 'Type': "CheckOut"}, {'$set': transaction_exist})

                            #after renewing, we have to update in the reservation.
                            reservation_exists = db.Reservation.find_one({"CopyId":CopyId})
                            if reservation_exists:
                                reservation_exists["ExpectedDate"] = str(date.today() + timedelta(days=30))
                                db.Reservation.update_one({"CopyId":CopyId}, {'$set': reservation_exists})
                            else:
                                #else insert a a new reservation document.
                                reserve_doc = {
                                    "StudentID": StudentId,
                                    "CopyId": CopyId,
                                    "ExpectedDate": str(date.today() + timedelta(days=30))
                                }

                                db.Reservation.insert_one(reserve_doc)
                            flash("Book Renewal Successful!!")
                            return "Book Renewal Successful!!"
                        
                        elif doc['RenewCount'] == 0:
                            return "Book Cannot Be Renewed!!"
            
            else :
                return "No Transaction Exists.."
            
        except Exception as e:
            print("Error:", str(e))
            return "Error occurred while renewing the Book: " + str(e)
    else:
        return redirect(url_for('home'))

@app.route('/profile/<string:id>')
def profile(id):
    if 'user' in session:
        try:
            user_profile = users.find_one({"_id": ObjectId(id)})
            return render_template('profile.html', user_profile=user_profile)
        except:
            return "Error in fetching the user profile!!" 
    else:
        return redirect(url_for('home'))


# Routes for Librarian

@app.route('/librarianAuth', methods=['GET', 'POST'])
def librarianAuth():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        librarian_data = db.Librarian.find_one({'email': email})

        if(librarian_data == None):
            flash("Librarian Data Not Found!! Try Signing Up!!!!")
            return render_template('librarianLogin.html')

        if(not (check_password_hash(librarian_data['password'], password))):
            flash("Invalid: Wrong Password!")
            return render_template('librarianLogin.html')

        if librarian_data and check_password_hash(librarian_data['password'], password):
            session['user'] = email
            return redirect(url_for('librarianDashboard'))

    return render_template('librarianLogin.html')

@app.route('/librarianDashboard', methods=['GET', 'POST'])
def librarianDashboard():
    if 'user' in session:
        if request.method == 'POST':
            StudentID = request.form['StudentID']
            try:
                user_result = db.users.find_one({'studentID': StudentID})
                if user_result:
                    return render_template('makePayment.html', user_result=user_result)
            except Exception as e:
                print("Error:", str(e))
                return "Please Make Sure The Student ID Is Correct: " + str(e)

        return render_template('librarianDashboard.html')
    else:
        return redirect(url_for('home'))

@app.route('/makePayment/<string:studentId>', methods=['GET', 'POST'])
def makePayment(studentId):
    if 'user' in session:
        if request.method == 'POST':
            amount = request.form['amount']

            if len(request.form['cardNumber']) == 16:
                card_doc = {
                    "Name": request.form['cardName'],
                    "Email": request.form['cardEmail'],
                    "CardNumber": request.form['cardNumber'],
                    "CVV": request.form['cardCVV']
                }
            else: 
                return "Invalid Card Number"

            user_result = db.users.find_one({'studentID': studentId})
            
            try:
                if user_result['due_amount'] > 0:
                    user_result['due_amount'] = int(user_result['due_amount']) - int(amount)
                    db.users.update_one({'studentID': studentId}, {'$set': user_result})
                    print("Amount Deducted Successfully.")

                elif user_result['due_amount'] == 0:
                    return "NO AMOUNT DUE"
            
                card_info_exists = db.Payment.find_one({'CardNumber': request.form['cardNumber']})
                if card_info_exists:
                    print("Card Info Already Exists!!!")
                else:
                    insert_result = db.Payment.insert_one(card_doc)
                    
                    if insert_result.acknowledged:
                        flash("Card Added Successfully.")
                        print("Card Added Successfully.")
                    
                    else:
                        print("Failed To Save Card Info!!")
                        flash("Invalid: Failed To Save Card Info!!")
                
            except Exception as e:
                print("Error:", str(e))
                return "Error occurred while making the payment: " + str(e)
            
            return render_template('librarianDashboard.html')
        
        return render_template('makePayment.html')
    else:
        return redirect(url_for('home'))

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if 'user' in session:
        if request.method == 'POST':
            StudentID = request.form['StudentID']
            bookID = request.form['bookID']
            location =  request.form['location']

            #change the avialability to true and also update the location and delete the record from reservation since it has been available.
            try:
                book = db.Copies.find_one({'CopyId': bookID})
                book_loc = db.CopyLocation.find_one({'CopyId': bookID})
                if book and book_loc:
                    book['Availability'] = True
                    book_loc['Location'] = location

                    db.Copies.update_one({'CopyId': bookID}, {'$set': book}) and db.CopyLocation.update_one({'CopyId': bookID}, {'$set': book_loc})
                    print("Availability changed successfully.")
                else:
                    return "Book with ID {} not found.".format(bookID)
                
                delete_reserv = db.Reservation.delete_one({'CopyId': bookID, 'StudentID': StudentID})
                if delete_reserv.acknowledged:
                    print("Info deleted from Reservation!!")
                else:
                    print("Failed to delete the info from Reservation DB")

            except Exception as e:
                print("Error:", str(e))
                return "Error occurred while updating the book location: " + str(e)
            
            #record a checkin transaction
            try:
                transaction_exist = db.Transaction.find_one({'StudentID': StudentID, 'Type': "CheckIn"})
                append_doc = {
                    "CopyId": request.form['bookID']
                }

                if transaction_exist:
                    transaction_exist['CopyList'].append(append_doc)
                    print("transaction_exist after appending the doc is: ",transaction_exist)
                    db.Transaction.update_one({'StudentID': StudentID, 'Type': "CheckIn"}, {'$set': transaction_exist})
                    flash("Book CheckIn Successfull.")
                
                #single book checkin
                else:
                    checkin_doc = {
                        "StudentID" : request.form['StudentID'],
                        "Type": "CheckIn",
                        "Date": str(date.today()),
                        "CopyList": [
                            {
                                "CopyId": request.form['bookID']
                            }
                        ]
                    }

                    try:
                        insert_result = db.Transaction.insert_one(checkin_doc)
                        if insert_result.acknowledged:
                            print("Book CheckIn Successfull.")
                        else:
                            flash("Invalid: Book CheckIn Failed")
                            print("Book CheckIn Failed")
                    except Exception as e:
                        print("Error:", str(e))
                        return "Error occurred while inserting CheckIn Transaction: " + str(e)
                
            except Exception as e:
                    print("Error:", str(e))
                    return "Error occurred while checking in the book: " + str(e)

            #if return date is greater than the expiresOn date --> update the due_amount of user and also remove from checkout transaction
            cur_date = date.today()

            transaction_exist = db.Transaction.find_one({'StudentID': StudentID, 'Type': "CheckOut"})
            if transaction_exist:
                list  = transaction_exist['CopyList']
                for doc in list:
                    if doc['CopyId'] == bookID:
                        expires_on = datetime.strptime(doc['ExpiresOn'], '%Y-%m-%d').date()
                        if  cur_date <= expires_on:
                            print("Checking In the Book Before Due Date")
                        else:
                            no_of_days = (cur_date - expires_on).days
                            amt_due = no_of_days * 10 #lets us consider 10$ per day as a late fee

                            user = db.users.find_one({'studentID': StudentID})
                            if user:
                                user['due_amount'] += amt_due #updated the user due amount based on the no of days late
                                db.users.update_one({'studentID': StudentID}, {'$set': user})
                                print("Late Fee {} Added To Users Profile!!".format(amt_due))
                            else:
                                print("Error Finding User In Users Collection!!")
                                return "Error Finding User In Users Collection!!"
                            
                        #after updating the users due_amount we have to delete the checkout record
                        list.remove(doc)
                        transaction_exist['CopyList'] = list
                        db.Transaction.update_one({'StudentID': StudentID}, {'$set': transaction_exist})
            else:
                print("No CheckOut Transaction Record Found!!")
                return "No CheckOut Transaction Record Found!!"

        return render_template('bookCheckin.html')
    else:
        return redirect(url_for('home'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' in session:
        if request.method == 'POST':
            StudentID = request.form['StudentID']
            bookID = request.form['bookID']
            reserve_doc = {
                "StudentID": StudentID,
                "CopyId": bookID,
                "ExpectedDate": str(date.today() + timedelta(days=30))
            }

            #changing the availability of the book to False
            book = db.Copies.find_one({'CopyId': bookID})
            if book:
                book['Availability'] = False

                db.Copies.update_one({'CopyId': bookID}, {'$set': book})
                print("Book updated successfully.")
            else:
                return "Book with ID {} not found.".format(bookID)

            #create a CheckOut Transaction

            #multi book checkout
            transaction_exist = db.Transaction.find_one({'StudentID': StudentID})
            append_doc = {
                "CopyId": request.form['bookID'],
                "ExpiresOn": str(date.today() + timedelta(days=30)),
                "RenewCount": 1
            }

            if transaction_exist and transaction_exist['Type'] == 'CheckOut':
                transaction_exist['CopyList'].append(append_doc)
                db.Transaction.update_one({'StudentID': StudentID}, {'$set': transaction_exist})

                #after checking Out, we have to update the reservation DB
                insert_reserv = db.Reservation.insert_one(reserve_doc)
                if insert_reserv.acknowledged:
                    print("Info saved to Reservation!!")
                else:
                    print("Failed to save into Reservation DB")
                
                flash("Book CheckOut Successfull!!")
            
            #single book checkout
            else:
                checkout_doc = {
                    "StudentID" : request.form['StudentID'],
                    "Type": "CheckOut",
                    "Date": str(date.today()),
                    "CopyList": [
                        {
                            "CopyId": request.form['bookID'],
                            "ExpiresOn": str(date.today() + timedelta(days=30)),
                            "RenewCount": 1
                        }
                    ]
                }

                try:
                    insert_result = db.Transaction.insert_one(checkout_doc)
                    
                    #after checking Out, we have to update the reservation DB
                    insert_reserv = db.Reservation.insert_one(reserve_doc)
                    if insert_reserv:
                        print("Info saved to Reservation!!")
                    else:
                        print("Failed to save into Reservation DB")

                    if insert_result:
                        flash("Book CheckOut Successfull!!")
                        print("Book CheckOut Successfull!!")
                    else:
                        flash("Invalid: Book CheckOut Failed")
                        print("Book CheckOut Failed")
                except Exception as e:
                    print("Error:", str(e))
                    return "Error occurred while checking out the book: " + str(e)

        return render_template('bookCheckout.html')
    
    else:
        return redirect(url_for('home'))


# Routes for Admin

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

@app.route('/addBook', methods=['GET','POST'])
def addBook():
    if 'user' in session:
        if request.method == 'POST':
            document = {
                'CopyId': request.form['bookID'],
                'Title': request.form['title'],
                'Author': request.form['author'],
                'Genre': request.form['genre'],
                'ISBN': request.form['isbn'],
                'Availability': True
            }

            cl_doc = {
                'CopyId': request.form['bookID'],
                'Location': request.form['location']
            }

            try:
                insert_result = db.Copies.insert_one(document) and db.CopyLocation.insert_one(cl_doc)
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
    else:
        return redirect(url_for('home'))

@app.route('/deleteBook', methods=['GET','POST'])
def deleteBook():
    if 'user' in session:
        if request.method == 'POST':
            try:
                book_id = request.form['bookID']
                isbn = request.form['isbn']
                location = request.form['location']

                book_in_copies = db.Copies.find_one({'CopyId': book_id, 'ISBN': isbn})
                book_in_copyLocation = db.CopyLocation.find_one({'CopyId': book_id, 'Location': location})

                if book_in_copies and book_in_copyLocation:
                    db.Copies.delete_one({'CopyId': book_id, 'ISBN': isbn}) and db.CopyLocation.delete_one({'CopyId': book_id, 'Location': location})
                    flash("Book deleted successfully.")
                else:
                    return "No book found with provided BookId, ISBN, and Location."

            except Exception as e:
                print("Error:", str(e))
                return "Error occurred while deleting the book: " + str(e)

        return render_template('deleteBook.html')
    else:
        return redirect(url_for('home'))

@app.route('/editBook', methods=['GET','POST'])
def editBook():
    if 'user' in session:
        try:
            if request.method == 'POST':
                book_id = request.form['bookID']
                book = db.Copies.find_one({'CopyId': book_id})
                book_cl = db.CopyLocation.find_one({'CopyId': book_id})
                if book and book_cl:
                    book['Title'] = request.form['title']
                    book['Author'] = request.form['author']
                    book['Genre'] = request.form['genre']
                    book['ISBN'] = request.form['isbn']
                    book_cl['Location'] = request.form['location']

                    db.Copies.update_one({'CopyId': book_id}, {'$set': book}) and db.CopyLocation.update_one({'CopyId': book_id}, {'$set': book_cl})
                    flash("Book updated successfully.")
                else:
                    return "Book with ID {} not found.".format(book_id)
        except Exception as e:
                print("Error:", str(e))
                return "Error occurred while editing the book: " + str(e)
        
        return render_template('editBook.html')
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

def send_email(sender_email, sender_password, receiver_email, subject, message):
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Create SMTP session
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    # Login
    server.login(sender_email, sender_password)

    # Send email
    server.sendmail(sender_email, receiver_email, msg.as_string())

    # Quit SMTP session
    server.quit()

if __name__ == '__main__':
    app.run(debug=True)
