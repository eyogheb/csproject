import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv("API.env")
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["Menu_DB"]
menu_collection = db["menu"]
orders_collection = db["orders"]
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")



try:
    client.admin.command('ping')
    print("Pinged your deployment. Successfully connected to MongoDB!")
except Exception as e:
    print(e)
