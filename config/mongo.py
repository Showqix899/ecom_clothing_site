import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv
load_dotenv()

client = MongoClient(
    os.getenv('MONGO_URI'),
    tls=True,
    tlsCAFile=certifi.where()
)

db = client['hexdexter47_db_user']
