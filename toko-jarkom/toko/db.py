import os

from pymongo import MongoClient

URI = os.environ.get('MONGODB_URI', 'mongodb://127.0.0.1:27018')
DATABASE_NAME = os.environ.get('MONGODB_DATABASE', 'toko')

client = MongoClient(
	URI,
	serverSelectionTimeoutMS=2000,
)
db = client[DATABASE_NAME]