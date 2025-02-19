import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


load_dotenv("API.env")
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["test"]
menu_collection = db["menu"]

# Initialize API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Initialize the AI model
llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0, max_retries=2)

# Shopping Cart (Initially Empty)
shopping_cart = {}

def get_menu_item(args) -> list:
    """Fetches menu items based on flexible search criteria (name, category, calorie limit, etc.)."""
    if isinstance(args, str):
        try:
            args = json.loads(args.replace("'", '"'))
        except json.JSONDecodeError:
            return []

    # Extract search filters
    item_name = args.get("item_name", "").strip().lower()
    category = args.get("category", "").strip().lower()
    max_calories = args.get("max_calories", None)

    # Build MongoDB query dynamically
    query = {}

    if item_name:
        query["name"] = {"$regex": f"^{item_name}$", "$options": "i"}

    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    if max_calories is not None:
        try:
            max_calories = int(max_calories)
            query["calories"] = {"$lte": max_calories}
        except ValueError:
            return "Invalid max_calories value. Please provide a number."

    # Execute query and fetch results
    items = list(menu_collection.find(query, {"_id": 0}))

    if not items:
        return "No matching items found."

    return items


def add_to_cart(args) -> str:
    """Adds an item to the shopping cart, allowing for modifications."""
    if isinstance(args, str):  
        try:
            args = json.loads(args.replace("'", '"'))
        except json.JSONDecodeError:
            return "Invalid input format. Please provide a valid item and quantity."

    item_name = args.get("item_name", "").strip().lower()
    quantity = int(args.get("quantity", 1))
    modifications = tuple(sorted(args.get("modifications", [])))  

    item = get_menu_item({"item_name": item_name})

    if not item:
        return f"Sorry, {item_name} is not available on the menu."

    cart_key = (item_name, modifications)

    if cart_key not in shopping_cart:
        shopping_cart[cart_key] = {"quantity": 0, "modifications": modifications}

    shopping_cart[cart_key]["quantity"] += quantity

    mod_text = f" with {' and '.join(modifications)}" if modifications else ""
    return f"Added {quantity}x {item_name}(s){mod_text} to your cart."

def remove_from_cart(args) -> str:
    """Removes a specific variant of an item from the shopping cart."""
    if isinstance(args, str):  
        try:
            args = json.loads(args.replace("'", '"'))
        except json.JSONDecodeError:
            return "Invalid input format. Please provide a valid item and quantity."

    item_name = args.get("item_name", "").strip().lower()  # Convert to lowercase
    quantity = int(args.get("quantity", 1))
    modifications = tuple(sorted(args.get("modifications", [])))

    # 🔹 Normalize the key lookup by converting stored keys to lowercase
    matching_key = None
    for key in shopping_cart.keys():
        if key[0].lower() == item_name and key[1] == modifications:
            matching_key = key
            break

    if not matching_key:
        return f"{item_name.capitalize()} with the specified modifications is not in your cart."

    # Remove the item or decrease its quantity
    if shopping_cart[matching_key]["quantity"] <= quantity:
        del shopping_cart[matching_key]  
        return f"Removed all {matching_key[0]}(s) {modifications} from your cart."
    else:
        shopping_cart[matching_key]["quantity"] -= quantity
        return f"Removed {quantity}x {matching_key[0]}(s) {modifications} from your cart."


def view_cart(args=None) -> dict:
    """Returns the raw contents of the shopping cart."""
    if isinstance(args, str):  
        try:
            args = json.loads(args.replace("'", '"'))  
        except json.JSONDecodeError:
            return {"error": "Invalid input format."}

    if isinstance(args, dict) and not args:
        args = None  

    if not shopping_cart:
        return {"message": "Your shopping cart is empty."}

    return shopping_cart


def load_menu_data():
    """Fetches all menu items from the database at startup."""
    menu_items = list(menu_collection.find({}, {"_id": 0}))  # Exclude MongoDB `_id` field

    # Organize items by category for better readability
    menu_by_category = {}
    for item in menu_items:
        category = item.get("category", "Uncategorized").lower()
        if category not in menu_by_category:
            menu_by_category[category] = []
        menu_by_category[category].append(item)

    return menu_items, menu_by_category

def do_nothing(args=None) -> str:
    """Handles cases where the user's input is unrelated to the menu or shopping cart."""
    return ""




# Load menu data at startup
full_menu, menu_by_category = load_menu_data()


# Register AI Tools
do_nothing_tool = Tool(
    "do_nothing",
    do_nothing,
    "Does nothing. When the user asks a question that is not related to the menu or shopping cart, kindly inform them that you are here to assist with menu items and their shopping cart.")
add_item_tool = Tool(
    "add_to_cart", 
    add_to_cart,
    "Adds an item to the cart. When adding multiple different items, add them one at a time. When adding an item with modifications, include the modifications make sure the modification is possible by referencing the list of available modifications for that item.")
remove_item_tool = Tool(
    "remove_from_cart", 
    remove_from_cart, 
    "Removes an item from the cart.")
view_cart_tool = Tool(
    "view_cart",
    view_cart, 
    "Displays the shopping cart.")
get_menu_item_tool = Tool(
    "get_menu_item",
    get_menu_item,
    "Retrieves menu items based on search criteria. Supports item_name (string), category (string), and max_calories (integer)."
)


# Create an AI Agent
agent = initialize_agent(
    tools=[add_item_tool, remove_item_tool, view_cart_tool, get_menu_item_tool, do_nothing_tool],  
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,  
)

menu_text = "\n".join([
    f"- {item['name']} ({item['category']}): ${item['price']:.2f}"
    for item in full_menu
])

message_history = [
    SystemMessage(content=(
        "You are a helpful AI assistant managing a shopping cart."
        " The current menu includes the following items:\n\n"
        f"{menu_text}\n\n"
        "You should use this knowledge to answer questions about the menu."
        " Always use get_menu_item to search for menu items."
        " When calling functions, DO NOT wrap JSON in backticks (`) or Markdown formatting."
        " Return JSON as plain text with no special characters."
        " Examples:"
        " - Correct: { \"category\": \"burgers\" }"
        " - Incorrect: {\"category\": \"burgers\"}"
        " Format responses as follows:"
        " Thought: (Explain your reasoning, no backticks)"
        " Action: (Choose one function, no backticks)"
        " Action Input: (Valid JSON, no backticks)"
        " Observation: (Function result, no backticks)"
        " Final Answer: (User-friendly response, no special formatting)"
        "When adding an item with modifications, include the modifications make sure the modification is possible by referencing the list of available modifications for that item. "
        "for example input should look like: { \"item_name\": \"Big Mac\", \"modifications\": [] the list of modifications may have any number, 0 or greater of unique modifications."
         " But it may not have contradictory modifications. For example, you may not have both \"no pickles\" and \"extra pickles\" in the same modification list."
         "Each request will include the message history, only the act on the most recent request, the rest of the history is for context."
         "When using view_cart, include the total cost for those items in the response."
         ""
         
    ))
]





print("\nAI-Powered Shopping Cart")
print("You can ask the AI to add or remove items, and check your cart.")
print("Type 'exit' or 'quit' to stop.\n")

while True:
    user_input = input("Your request: ")

    if user_input.lower() in ["exit", "quit"]:
        print("\nThank you for shopping! Have a great day!")
        break

    message_history.append(HumanMessage(content=user_input))

    try:
        response = agent.invoke({"input": message_history})  
        ai_response = response["output"]

        message_history.append(AIMessage(content=ai_response))

        print(f"\nAI Response: {ai_response}\n")
        print(message_history)
        print(shopping_cart.items())
    except Exception as e:
        print(f"\nError: {str(e)}\n")