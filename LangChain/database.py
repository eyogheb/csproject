import json
import re
from config import menu_collection, orders_collection
from datetime import datetime, UTC


def load_menu_data(): # This is not a tool used by the Agent, but we load the menu items and categories for it on startup to reduce the number of database calls
    menu_items = list(menu_collection.find({}, {"_id": 0}))  # Exclude MongoDB `_id` field

    # Organize items by category for better readability
    menu_by_category = {}
    for item in menu_items:
        category = item.get("category", "Uncategorized").lower() # This block gets every menu item and sorts them by category and outputs a dictionary with them that we hand to the agent on start up
        if category not in menu_by_category:
            menu_by_category[category] = []
        menu_by_category[category].append(item)

    return menu_items, menu_by_category

def get_menu_item(args) -> list:

    try:
        if isinstance(args, str):
            args = json.loads(args)
    except json.JSONDecodeError:
        return "Invalid JSON format for menu item search."

    # Extract search filters
    item_name = args.get("item_name", "").strip().lower()
    category = args.get("category", "").strip().lower()
    max_calories = args.get("max_calories", None)      # These are what the agent is searching for, so if the user asks for an item it will use item name, if they ask for a category it will use category, etc.

    # Build MongoDB query dynamically
    query = {}

    if item_name:
        query["name"] = {"$regex": re.escape(item_name), "$options": "i"}   # This is the query that the agent will use to search for the item in the database the regex part makes it search for the exact name
                                                                        # The $options: "i" makes it case insensitive
    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    if max_calories is not None:
        try:
            max_calories = int(max_calories)
            query["calories"] = {"$lte": max_calories}  # This query lets the user ask for items with less than for example 400 calories
        except ValueError:
            return "Invalid max_calories value. Please provide a number."

    # Execute query and fetch results
    items = list(menu_collection.find(query, {"_id": 0}))  # THis executes the query and fetches the results from the database

    if not items:
        return "No matching items found." # If it cant find any items matching the query it will return this

    return items   # Otherwise it returns the items it found

def place_order(order_data):
    """
    Accepts a JSON string or dict containing items, adds a timestamp-based ID, and stores it in orders_collection.
    """
    try:
        # Parse the input if it's a JSON string
        if isinstance(order_data, str):
            order_data = json.loads(order_data)
    except json.JSONDecodeError:
        return "Invalid JSON format for order."

    if not isinstance(order_data, dict):
        return "Order data must be a dictionary."

    items = order_data.get("cart")
    if not isinstance(items, list) or not items:
        return "Order must include a non-empty list of items."

    # Add timestamp-based order ID and creation time
    now = datetime.now(UTC).isoformat()
    order_data["created_at"] = now

    try:
        orders_collection.insert_one(order_data)
        return f"Order placed successfully with ID: {order_data['order_id']}"
    except Exception as e:
        return f"Failed to place order: {str(e)}"