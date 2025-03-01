import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv("API.env")
uri = os.getenv("MONGODB_URI") # Loads the MongoDB URI from the environment
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["Menu_DB"]
menu_collection = db["menu"]    # This is the database we are using

# Initialize API keys
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY") # Loads the GROQ API key from the environment


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

def add_combo(args) -> str:

    if isinstance(args, str):
        args = json.loads(args)

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

    if isinstance(args, str):
        args = json.loads(args)

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
    "Retrieves menu items based on search criteria. Supports item_name (string), category (string), and max_calories (integer). Use this tool to look up information on menu items")
add_combo_tool = Tool( # maybe need to revise the description for this and remove combo, sometimes the agent formats the input wrong, but we cant give an explicit example, it breaks the description
    "add_combo",
    add_combo,
    (
        "Adds a combo to the cart. A combo must include one entree, one side, and one drink. "
        "This combo provides a 10% discount on the total price. "
        "To add a combo, specify: "
        "- Entree and any modifications "
        "- Side and any modifications "
        "- Drink and any modifications "
        "- Quantity of the combo to add "
        "You should format the input on one line"
    ))
remove_combo_tool = Tool(
    "remove_combo",
    remove_combo,
    (
        "Removes a combo from the cart. A combo must include one entree, one side, and one drink. "
        "To remove a combo, specify: "
        "- Entree name and any modifications "
        "- Side name and any modifications "
        "- Drink name and any modifications "
        "- Quantity of the combo to remove "
        "You should format the input on one line"
        "The input should consist of 3 dictionaries, one for each item in the combo, with each containing for example \"item_name\": \"Big Mac\", \"modifications\": []"
    ))
do_nothing_tool = Tool(
    "do_nothing",
    do_nothing,
    "Does nothing. Get past the action stage without performing any action."
)




menu_text = "\n".join([ # This block just formats the menu items for the agent to use
    f"- {item['name']} ({item['category']}): ${item['price']:.2f}"
    for item in full_menu
]) 



prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful AI assistant managing a shopping cart. "
            "The current menu includes the following items:\n\n" +
            menu_text +
            "\n\nYou should use this knowledge to answer questions about the menu. "
            "Always use get_menu_item to search for menu items. "
            "When calling functions, DO NOT wrap JSON in backticks or Markdown formatting. "
            "When adding an item with modifications, ensure the modifications are valid. "
            "If a user adds an entree, kindly ask if they would like to make it a combo after adding the entree. "
            "If the user agrees to make it a combo, remove the entree from the cart and add the combo instead."
            "If the user asks about a menu item, look up the item using get_menu_item and answer based on its details."
            "If the user wants to change an item in their cart, remove the item and add the new item, but be sure to check if the modifications are valid."
            "Your response must follow the pattern of thought -> action -> response. "
            "If you already know the correct response you may use do_nothing, but if you have any other relevent tool to use, you should use it."
            "IMPORTANT: when you use a tool, you must use the results"
            "IMPORTANT: Dont wrap thoughts with anything (for example **)",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)


# Create an AI Agent
agent = initialize_agent(
    tools=[add_item_tool, remove_item_tool, view_cart_tool, get_menu_item_tool, remove_combo_tool, add_combo_tool, do_nothing_tool], # The list of tools we are giving it 
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, # We use this type because we want the agent to think before it takes its action
    verbose=True, # This makes the AI print its thoughts to console
    handle_parsing_errors=True,  
)

def call_model(state: MessagesState):
    prompt = prompt_template.invoke(state)
    messages = prompt.to_messages()  # Convert the prompt to the required list format
    result = agent.invoke(messages)
    
    # LangChain requires the response to be in a dict with role and content fields, our agent just returns output, so we format the response here for LangChain
    if isinstance(result, dict) and "input" in result and "output" in result:
        # If the agent returns a dict with 'input' and 'output', wrap the output properly.
        formatted = [{"role": "assistant", "content": result["output"]}]
    elif isinstance(result, str):
        # If it's a simple string, wrap it.
        formatted = [{"role": "assistant", "content": result}]
    elif isinstance(result, list):
        # If it's a list, ensure each element is a dict with 'role' and 'content'
        formatted = []
        for r in result:
            if isinstance(r, dict) and "role" in r and "content" in r:
                formatted.append(r)
            elif isinstance(r, dict) and "input" in r and "output" in r:
                formatted.append({"role": "assistant", "content": r["output"]})
            else:
                formatted.append({"role": "assistant", "content": str(r)})
    else:
        formatted = [{"role": "assistant", "content": str(result)}]
    
    return {"messages": formatted}


workflow = StateGraph(state_schema=MessagesState) 
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)# all of this workflow stuff lets LangChain manage the memory for us

config = {"configurable": {"thread_id": "abc345"}}# we can use this later with a variable for thread id to let multiple users keep their conversations distinct
                       
print("\nAI-Powered Shopping Cart") # Some dummy text mostly to remind that exit and quit break the loop
print("You can ask the AI to add or remove items, and check your cart.")
print("Type 'exit' or 'quit' to stop.\n")

while True: # do forever
    user_input = input("Your request: ")

    if user_input.lower() in ["exit", "quit"]:
        print("\nThank you for shopping! Have a great day!")
        break

    try:
        input_messages = [HumanMessage(user_input)]
        output = app.invoke({"messages": input_messages}, config)
        output["messages"][-1].pretty_print()
        print(shopping_cart.items()) # This prints the cart as it currently is, this is just here for debugging purposes
    except Exception as e:
        print(f"\nError: {str(e)}\n")