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
uri = os.getenv("MONGODB_URI") # Loads the MongoDB URI from the environment
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["Menu_DB"]
menu_collection = db["menu"]    # This is the database we are using

# Initialize API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Loads the GROQ API key from the environment
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

try:       # This block just checks the connection to the database
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Initialize the AI model
llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0, max_retries=2) #This defines the AI model we are using, and sets temperature and max_retries. 
                                                                                    #Temperature defines how creative the AI is and retries is how many times it will try generating a response.

# Shopping Cart (Initially Empty)
shopping_cart = {}

def get_menu_item(args) -> list:

    if isinstance(args, str): # This block just puts the args in json format
        args = json.loads(args)

    # Extract search filters
    item_name = args.get("item_name", "").strip().lower()
    category = args.get("category", "").strip().lower()
    max_calories = args.get("max_calories", None)      # These are what the agent is searching for, so if the user asks for an item it will use item name, if they ask for a category it will use category, etc.

    # Build MongoDB query dynamically
    query = {}

    if item_name:
        query["name"] = {"$regex": f"^{item_name}$", "$options": "i"}   # This is the query that the agent will use to search for the item in the database the regex part makes it search for the exact name
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


def add_to_cart(args) -> str:

    if isinstance(args, str):
        args = json.loads(args)

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

    if isinstance(args, str):
        args = json.loads(args)
    
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

    return shopping_cart # This just prints the shopping cart for the agent


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

def do_nothing(args=None) -> str: # This function lets the agent do nothing if the query is unrelated to the menu or shopping cart
                                  # This is needed because the general flow of a LangChain agent is Prompt -> Thought -> Action -> Response
                                  # So this is a do nothing "Action"
    return ""




# Load menu data at startup
full_menu, menu_by_category = load_menu_data()


# Register AI Tools
do_nothing_tool = Tool(  #The general formal is Tool(name, function, description), the Agent uses the description to decide which tool to use
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
    "Retrieves menu items based on search criteria. Supports item_name (string), category (string), and max_calories (integer). Use this tool to look up information on menu items"
)


# Create an AI Agent
agent = initialize_agent(
    tools=[add_item_tool, remove_item_tool, view_cart_tool, get_menu_item_tool, do_nothing_tool], # The list of tools we are giving it 
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, # We use this type because we want the agent to think before it takes its action
    verbose=True, # This makes the AI print its thoughts to console
    handle_parsing_errors=True,  
)

menu_text = "\n".join([ # This block just formats the menu items for the agent to use
    f"- {item['name']} ({item['category']}): ${item['price']:.2f}"
    for item in full_menu
]) 

message_history = [  # This block is the startup message we send to the agent explaining what it is and what it should
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





print("\nAI-Powered Shopping Cart") # Some dummy text mostly to remind that exit and quit break the loop
print("You can ask the AI to add or remove items, and check your cart.")
print("Type 'exit' or 'quit' to stop.\n")

while True: # do forever
    user_input = input("Your request: ")

    if user_input.lower() in ["exit", "quit"]:
        print("\nThank you for shopping! Have a great day!")
        break

    message_history.append(HumanMessage(content=user_input)) # Currently the message history is a list of all messages sent to and from the agent, we add the new query to the list

    try:
        response = agent.invoke({"input": message_history})  # this sends the message history and the new query to the agent and gets the response
        ai_response = response["output"] # This is mostly for formatting in the message_history, it gets the actual response from the tuple that the agent returns

        message_history.append(AIMessage(content=ai_response))

        print(f"\nAI Response: {ai_response}\n") # This prints the response to the console
        print(shopping_cart.items()) # THis prints the cart as it currently is, this is just here for debugging purposes
    except Exception as e:
        print(f"\nError: {str(e)}\n")