import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv("API.env")
uri = os.getenv("MONGODB_URI")
print(uri)
client = MongoClient(uri, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Connection Error:",e)

db = client["Menu_DB"]  # Database name
menu_collection = db["menu"]  # Collection name

menu_data = [
    {
        "name": "Big Mac",
        "category": "Burgers",
        "price": 5.29,
        "ingredients": [
            "Sesame seed bun",
            "Beef patties",
            "Big Mac Sauce",
            "Iceberg lettuce",
            "American cheese",
            "Pickles",
            "Onions"
        ],
        "calories": 590,
        "modifications": ["no pickles", "no onions", "no cheese", "no lettuce", "no sauce", "extra sauce", "extra cheese", "extra lettuce", "extra onions", "extra pickles"],
        "type": "entree"
    },
    {
        "name": "Quarter Pounder with Cheese",
        "category": "Burgers",
        "price": 6.39,
        "ingredients": [
            "Sesame seed bun",
            "Beef patty",
            "American cheese",
            "Onions",
            "Pickles",
            "Ketchup",
            "Mustard"
        ],
        "calories": 520,
        "modifications": ["no pickles", "no onions", "no cheese", "no ketchup", "no mustard", "extra cheese", "extra onions", "extra pickles"],
        "type": "entree"
    },
    {
        "name": "Double Quarter Pounder with Cheese",
        "category": "Burgers",
        "price": 7.49,
        "ingredients": [
            "Sesame seed bun",
            "Beef patties",
            "American cheese",
            "Onions",
            "Pickles",
            "Ketchup",
            "Mustard"
        ],
        "calories": 740,
        "modifications": ["no pickles", "no onions", "no cheese", "extra cheese", "extra pickles"],
        "type": "entree"
    },
    {
        "name": "Cheeseburger",
        "category": "Burgers",
        "price": 2.99,
        "ingredients": [
            "Bun",
            "Beef patty",
            "American cheese",
            "Pickles",
            "Onions",
            "Ketchup",
            "Mustard"
        ],
        "calories": 300,
        "modifications": ["no pickles", "no onions", "no cheese", "no ketchup", "no mustard", "extra cheese", "extra pickles"],
        "type": "entree"
    },
    {
        "name": "McChicken",
        "category": "Chicken & Fish Sandwiches",
        "price": 3.49,
        "ingredients": [
            "Bun",
            "Chicken patty",
            "Mayonnaise",
            "Lettuce"
        ],
        "calories": 400,
        "modifications": ["no lettuce", "no mayonnaise", "extra mayonnaise", "extra lettuce"],
        "type": "entree"
    },
    {
        "name": "Spicy McChicken",
        "category": "Chicken & Fish Sandwiches",
        "price": 3.79,
        "ingredients": [
            "Bun",
            "Chicken patty",
            "Mayonnaise",
            "Lettuce"
        ],
        "calories": 410,
        "modifications": ["no lettuce", "no mayonnaise", "extra mayonnaise", "extra lettuce"],
        "type": "entree"
    },
    {
        "name": "Filet-O-Fish",
        "category": "Chicken & Fish Sandwiches",
        "price": 4.99,
        "ingredients": [
            "Bun",
            "Fish patty",
            "American cheese",
            "Tartar sauce"
        ],
        "calories": 380,
        "modifications": ["no cheese", "no tartar sauce", "extra tartar sauce", "extra cheese"],
        "type": "entree"
    },
    {
        "name": "10 piece Chicken McNuggets",
        "category": "McNuggets & Meals",
        "price": 5.49,
        "ingredients": [
            "Chicken",
            "Breading",
            "Seasoning",
            "Oil"
        ],
        "calories": 420,
        "modifications": ["choice of dipping sauce"],
        "type": "entree"
    },
    {
        "name": "French Fries (Small)",
        "category": "Sides",
        "price": 1.91,
        "ingredients": [
            "Potatoes",
            "Vegetable oil",
            "Beef flavoring",
            "Salt"
        ],
        "calories": 230,
        "modifications": ["no salt", "extra salt"],
        "type": "side"
    },
    {
        "name": "French Fries (Medium)",
        "category": "Sides",
        "price": 2.99,
        "ingredients": [
            "Potatoes",
            "Vegetable oil",
            "Beef flavoring",
            "Salt"
        ],
        "calories": 320,
        "modifications": ["no salt", "extra salt"],
        "type": "side"
    },
    {
        "name": "French Fries (Large)",
        "category": "Sides",
        "price": 3.59,
        "ingredients": [
            "Potatoes",
            "Vegetable oil",
            "Beef flavoring",
            "Salt"
        ],
        "calories": 480,
        "modifications": ["no salt", "extra salt"],
        "type": "side"
    },
    {
        "name": "Apple Slices",
        "category": "Sides",
        "price": 0.71,
        "ingredients": ["Apple"],
        "calories": 15,
        "modifications": [],
        "type": "side"
    },
    {
        "name": "Coca-Cola (Medium)",
        "category": "Beverages",
        "price": 1.99,
        "ingredients": [
            "Carbonated water",
            "High fructose corn syrup",
            "Caramel color",
            "Phosphoric acid",
            "Natural flavors",
            "Caffeine"
        ],
        "calories": 150,
        "modifications": ["no ice", "light ice"],
        "type": "drink"
    },
    {
        "name": "Sprite (Medium)",
        "category": "Beverages",
        "price": 1.99,
        "ingredients": [
            "Carbonated water",
            "High fructose corn syrup",
            "Citric acid",
            "Natural flavors",
            "Sodium citrate"
        ],
        "calories": 140,
        "modifications": ["no ice", "light ice"],
        "type": "drink"
    },
    {
        "name": "Iced Coffee",
        "category": "Beverages",
        "price": 2.49,
        "ingredients": [
            "Coffee",
            "Cream",
            "Sugar",
            "Ice"
        ],
        "calories": 180,
        "modifications": ["no sugar", "extra cream", "extra sugar"],
        "type": "drink"
    }
]

# Insert data into MongoDB
menu_collection.insert_many(menu_data)
print("Menu inserted successfully!")
