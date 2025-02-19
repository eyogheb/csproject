import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv("API.env")
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["test"]  # Database name
menu_collection = db["menu"]  # Collection name


menu_data = [
  {
    "name": "Big Mac",
    "category": "Burgers",
    "price": 5.29,
    "description": "A 100% beef burger with two beef patties, Big Mac Sauce, pickles, lettuce, onions, American cheese, and a sesame seed bun.",
    "calories": 590,
    "modifications": ["no pickles", "no onions", "no cheese", "no lettuce", "no sauce", "extra sauce", "extra cheese", "extra lettuce", "extra onions", "extra pickles"]
  },
  {
    "name": "Quarter Pounder with Cheese",
    "category": "Burgers",
    "price": 6.39,
    "description": "A quarter-pound* of 100% fresh beef, seasoned and sizzled on the grill, topped with slivered onions, tangy pickles, and two slices of melty American cheese.",
    "calories": 520,
    "modifications": ["no pickles", "no onions", "no cheese", "no ketchup", "no mustard", "extra cheese", "extra onions", "extra pickles"]
  },
  {
    "name": "Double Quarter Pounder with Cheese",
    "category": "Burgers",
    "price": 7.49,
    "description": "Two quarter-pound beef patties, American cheese, onions, pickles, mustard, and ketchup on a sesame seed bun.",
    "calories": 740,
    "modifications": ["no pickles", "no onions", "no cheese", "extra cheese", "extra pickles"]
  },
  {
    "name": "Cheeseburger",
    "category": "Burgers",
    "price": 2.99,
    "description": "A classic McDonald's Cheeseburger with a 100% beef patty, American cheese, pickles, onions, ketchup, and mustard.",
    "calories": 300,
    "modifications": ["no pickles", "no onions", "no cheese", "no ketchup", "no mustard", "extra cheese", "extra pickles"]
  },
  {
    "name": "McChicken",
    "category": "Chicken & Fish Sandwiches",
    "price": 3.49,
    "description": "A crispy chicken sandwich topped with mayonnaise and shredded lettuce, served on a perfectly toasted bun.",
    "calories": 400,
    "modifications": ["no lettuce", "no mayonnaise", "extra mayonnaise", "extra lettuce"]
  },
  {
    "name": "Spicy McChicken",
    "category": "Chicken & Fish Sandwiches",
    "price": 3.79,
    "description": "A spicy, crispy chicken sandwich with mayonnaise and shredded lettuce on a toasted bun.",
    "calories": 410,
    "modifications": ["no lettuce", "no mayonnaise", "extra mayonnaise", "extra lettuce"]
  },
  {
    "name": "Filet-O-Fish",
    "category": "Chicken & Fish Sandwiches",
    "price": 4.99,
    "description": "A wild-caught Alaskan Pollock fish fillet, melty American cheese, and tartar sauce on a soft, steamed bun.",
    "calories": 380,
    "modifications": ["no cheese", "no tartar sauce", "extra tartar sauce", "extra cheese"]
  },
  {
    "name": " 10 piece Chicken McNuggets",
    "category": "McNuggets & Meals",
    "price": 5.49,
    "description": "10 pieces of tender, juicy Chicken McNuggets made with 100% white meat chicken, served with dipping sauces.",
    "calories": 420,
    "modifications": ["choice of dipping sauce"]
  },
  {
    "name": "French Fries (Small)",
    "category": "Sides",
    "price": 1.91,
    "description": "Golden and crispy fries made with premium potatoes.",
    "calories": 230,
    "modifications": ["no salt", "extra salt"]
  },
   {
    "name": "French Fries (Medium)",
    "category": "Sides",
    "price": 2.99,
    "description": "Golden and crispy fries made with premium potatoes.",
    "calories": 320,
    "modifications": ["no salt", "extra salt"]
  },
   {
    "name": "French Fries (Large)",
    "category": "Sides",
    "price": 3.59,
    "description": "Golden and crispy fries made with premium potatoes.",
    "calories": 480,
    "modifications": ["no salt", "extra salt"]
  },

  {
    "name": "Apple Slices",
    "category": "Sides",
    "price": .71,
    "description": "A healthy snack with fresh apple slices.",
    "calories": 15,
    "modifications": []
  },
  {
    "name": "Coca-Cola (Medium)",
    "category": "Beverages",
    "price": 1.99,
    "description": "A classic and refreshing Coca-Cola served cold.",
    "calories": 150,
    "modifications": ["no ice", "light ice"]
  },
  {
    "name": "Sprite (Medium)",
    "category": "Beverages",
    "price": 1.99,
    "description": "A crisp and refreshing lemon-lime soda.",
    "calories": 140,
    "modifications": ["no ice", "light ice"]
  },
  {
    "name": "Iced Coffee",
    "category": "Beverages",
    "price": 2.49,
    "description": "McDonald's Iced Coffee, made with premium roast coffee, cream, and liquid sugar.",
    "calories": 180,
    "modifications": ["no sugar", "extra cream", "extra sugar"]
  }
]


# Insert data into MongoDB
menu_collection.insert_many(menu_data)
print("Menu inserted successfully!")