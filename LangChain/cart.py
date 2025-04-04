# Shopping Cart (Initially Empty)
import json
from database import get_menu_item
from datetime import datetime, timezone
from config import orders_collection



shopping_cart = {}

def add_to_cart(args) -> str:

    try:
        if isinstance(args, str):
            args = json.loads(args)
    except json.JSONDecodeError:
        return "Invalid JSON format for adding to cart."

    item_name = args.get("item_name", "").strip().lower() # Convert to lowercase
    quantity = int(args.get("quantity", 1)) # Convert to integer
    modifications = tuple(sorted(args.get("modifications", [])))   # converts modifications to a tuple and sorts them

    item = get_menu_item({"item_name": item_name}) # Fetch the item from the database

    if not item: #If we cant find the item in the database
        return f"Sorry, {item_name} is not available on the menu."

    cart_key = (item_name, modifications) # We use this instead of just name so that we can have multiple items with the same name but different modifications

    if cart_key not in shopping_cart: # If the item is not in the cart we add it with quantity 0
        shopping_cart[cart_key] = {"quantity": 0, "modifications": modifications}

    shopping_cart[cart_key]["quantity"] += quantity # If the item is in the cart we increase the quantity

    mod_text = f" with {' and '.join(modifications)}" if modifications else "" # THis is for the response to the user, it adds the modifications to the response
    return f"Added {quantity}x {item_name}(s){mod_text} to your cart."

def remove_from_cart(args) -> str:

    try:
        if isinstance(args, str):
            args = json.loads(args)
    except json.JSONDecodeError:
        return "Invalid JSON format for removing from cart."
    
    item_name = args.get("item_name", "").strip().lower()  # Convert to lowercase
    quantity = int(args.get("quantity", 1)) # Convert to integer
    modifications = tuple(sorted(args.get("modifications", []))) # Converts modifications to a tuple and sorts them

    #  This block searches each item in the cart to find a matching item (Both name and modifications)
    matching_key = None
    for key in shopping_cart.keys():
        if key[0].lower() == item_name and key[1] == modifications:
            matching_key = key
            break

    if not matching_key: # If it cant find the item in the cart it will return this
        return f"{item_name.capitalize()} with the specified modifications is not in your cart."

    # Remove the item or decrease its quantity
    if shopping_cart[matching_key]["quantity"] <= quantity: # THis is if we try to remove all of the item, or more than we have in the cart
        del shopping_cart[matching_key]  
        return f"Removed all {matching_key[0]}(s) {modifications} from your cart."
    else:
        shopping_cart[matching_key]["quantity"] -= quantity # This is if we only remove some of the item, but not all
        return f"Removed {quantity}x {matching_key[0]}(s) {modifications} from your cart."


def view_cart(args=None) -> dict:

    if not shopping_cart:
        return {"message": "Your shopping cart is empty."}

    return {"cart": shopping_cart} # This just prints the shopping cart for the agent

def add_combo(args) -> str:

    try:
        if isinstance(args, str):
            args = json.loads(args)
    except json.JSONDecodeError:
        return "Invalid JSON format for adding a combo."

    # Check if all required combo keys are present
    if "entree" not in args or "side" not in args or "drink" not in args:
        return "Incomplete combo specification. Please provide an entree, a side, and a drink to form a combo."

    quantity = int(args.get("quantity", 1))#We extract the items and their modifications as well as the quantity
    entree_data = args.get("entree", {})
    side_data = args.get("side", {})
    drink_data = args.get("drink", {})

    if not entree_data or not side_data or not drink_data: #ensures we have all 3 parts of a combo
        return "Combo must include one entree, one side, and one drink."

    # Extract item names and modifications
    entree_item_name = entree_data.get("item_name", "").strip().lower() #extract the name and modifications into separate variables
    side_item_name = side_data.get("item_name", "").strip().lower()
    drink_item_name = drink_data.get("item_name", "").strip().lower()
    entree_mods = tuple(sorted(entree_data.get("modifications", [])))
    side_mods = tuple(sorted(side_data.get("modifications", [])))
    drink_mods = tuple(sorted(drink_data.get("modifications", [])))

    # Fetch each menu item (Ensures they exist)
    entree_result = get_menu_item({"item_name": entree_item_name}) # This has the agent query the menu so we can ensure we have the right items and make sure they are the right types (entree, side, and drink)
    side_result = get_menu_item({"item_name": side_item_name})
    drink_result = get_menu_item({"item_name": drink_item_name})

    if not (isinstance(entree_result, list) and entree_result):
        return f"Entree item '{entree_item_name}' not found."
    if not (isinstance(side_result, list) and side_result):
        return f"Side item '{side_item_name}' not found."
    if not (isinstance(drink_result, list) and drink_result):
        return f"Drink item '{drink_item_name}' not found."

    # Extract the first matching item from each query result
    entree_item = entree_result[0]#the result is returned as a list of all matching items, so we select the first (should be only one result as names are unique)
    side_item = side_result[0]
    drink_item = drink_result[0]

    # Validate item types
    if entree_item.get("type", "").lower() != "entree":
        return f"Item '{entree_item_name}' is not an entree."
    if side_item.get("type", "").lower() != "side":
        return f"Item '{side_item_name}' is not a side."
    if drink_item.get("type", "").lower() != "drink":
        return f"Item '{drink_item_name}' is not a drink."

    # Calculate combo price with a 10% discount
    combo_price = (entree_item["price"] + side_item["price"] + drink_item["price"]) * 0.9

    # Create a structured key for the combo
    combo_key = (
        "combo",
        (entree_item_name, entree_mods),
        (side_item_name, side_mods),
        (drink_item_name, drink_mods),
    ) #we use this to see if an instance of the combo is in the cart already

    # Store only essential details in the shopping cart
    if combo_key not in shopping_cart:
        shopping_cart[combo_key] = {
            "quantity": 0,
            "items": {
                "entree": {"name": entree_item_name, "modifications": entree_mods},
                "side": {"name": side_item_name, "modifications": side_mods},
                "drink": {"name": drink_item_name, "modifications": drink_mods},
            },
            "price_per_combo": combo_price,
        }

    shopping_cart[combo_key]["quantity"] += quantity # add the order to the cart

    return (f"Added {quantity} combo(s) including {entree_item_name}, {side_item_name}, and {drink_item_name} "
            f"with a 10% discount to your cart. Price per combo: ${combo_price:.2f}")


def remove_combo(args) -> str: # this is the same as add_combo, but instead of adding quantity we remove it, and if the resulting quantity is zero, we remove the entry from the cart

    try:
        if isinstance(args, str):
            args = json.loads(args)
    except json.JSONDecodeError:
        return "Invalid JSON format for removing a combo."

    quantity = int(args.get("quantity", 1))
    entree_data = args.get("entree", {})
    side_data = args.get("side", {})
    drink_data = args.get("drink", {})

    if not entree_data or not side_data or not drink_data:
        return "Combo removal must include one entree, one side, and one drink."

    # Extract details and modifications
    entree_item_name = entree_data.get("item_name", "").strip().lower()
    side_item_name = side_data.get("item_name", "").strip().lower()
    drink_item_name = drink_data.get("item_name", "").strip().lower()
    entree_mods = tuple(sorted(entree_data.get("modifications", [])))
    side_mods = tuple(sorted(side_data.get("modifications", [])))
    drink_mods = tuple(sorted(drink_data.get("modifications", [])))

    # Build the combo key (same format as in add_combo)
    combo_key = (
        "combo",
        (entree_item_name, entree_mods),
        (side_item_name, side_mods),
        (drink_item_name, drink_mods),
    )

    if combo_key not in shopping_cart:
        return f"Combo including {entree_item_name}, {side_item_name}, and {drink_item_name} is not in your cart."

    # Remove or decrease the combo quantity
    if shopping_cart[combo_key]["quantity"] <= quantity:
        del shopping_cart[combo_key]
        return f"Removed all combos including {entree_item_name}, {side_item_name}, and {drink_item_name} from your cart."
    else:
        shopping_cart[combo_key]["quantity"] -= quantity
        return f"Removed {quantity} combo(s) including {entree_item_name}, {side_item_name}, and {drink_item_name} from your cart."
    

def place_order():
    """
    Accepts a JSON string or dict containing items, adds a timestamp-based ID, and stores it in orders_collection.
    """
    
    print("hi")

    # Add timestamp-based order ID and creation time
    now = datetime.now(timezone.utc).isoformat()
    shopping_cart["created_at"] = now
    print("hi2")

    try:
        orders_collection.insert_one(shopping_cart)
        return f"Order placed successfully"
    except Exception as e:
        return f"Failed to place order: {str(e)}"
