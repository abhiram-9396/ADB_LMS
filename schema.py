from flask import Flask
from pymongo import MongoClient

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'Abhiram'

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["LMS"]
    print("Database Connection Established!!")
except:
    print("Unable to Connect to the Database!!")

try:
    db.create_collection('Books', validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["BookId", "Title", "Author", "Genre", "ISBN", "Availability", "Branch", "Location", "WaitingList"],
        "properties": {
            "BookId": {"bsonType": "string", "description": "must be a string and is required"},
            "Title": {"bsonType": "string", "description": "must be a string and is required"},
            "Author": {"bsonType": "string", "description": "must be a string and is required"},
            "Genre": {"bsonType": "string", "description": "must be a string and is required"},
            "ISBN": {"bsonType": "string", "description": "must be a string and is required"},
            "Availability": {"bsonType": "bool", "description": "must be a boolean and is required"},
            "Branch": {"enum": ["Lee's Summit", "Warrensburg"], "description": "must be one of the enum values and is required"},
            "Location": {"bsonType": "string", "description": "must be a string and is required"},
            "WaitingList": {"bsonType": "int", "description": "must be an integer and is required"}
        }
    }
    })
    print("Collection 'Books' created with validation schema.")
except:
    print("Error in creating 'Books' collection")

