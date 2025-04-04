from langchain_community.tools import Tool
from database import get_menu_item
from cart import add_to_cart, remove_from_cart, view_cart, add_combo, remove_combo, place_order


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
place_order_tool = Tool(
    "place_order",
    place_order,
    "Places an order with the items in the cart. The order will be stored in the database.")


tools = [add_item_tool, remove_item_tool, view_cart_tool, get_menu_item_tool, add_combo_tool, remove_combo_tool, place_order_tool]