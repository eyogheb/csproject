from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, AgentType
from tools import tools
from database import load_menu_data, menu_collection
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI


# Load menu data at startup
full_menu, menu_by_category = load_menu_data()

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
            "When adding an item with modifications, ensure the modifications are valid. "
            "IMPORTANT: Allways use JSON formatting when taking an action"
            "If a user adds an entree, kindly ask if they would like to make it a combo after adding the entree."
            "Do not make assumptions about what the items the user wants when making a combo, if they do not tell you, ask them"
            "When calling add_combo or remove_combo, the input should be one JSON object with three keys: entree, side, and drink. Each key should contain a dictionary with the item name and modifications. A fourth key, quantity, is optional, if not provided it defaults to one"
            "If the user agrees to make it a combo, remove the entree from the cart and add the combo instead. Otherwise just leave it as is."
            "If the user asks about a menu item, look up the item using get_menu_item and answer based on its details."
            "If the user wants to change an item in their cart, remove the item and add the new item, but be sure to check if the modifications are valid."
            "IMPORTANT: when you use a tool, you must use the results"
            "If a user query is unrelated to the menu or cart, kindly inform them that you can only assist with menu and cart-related questions."
            "When providing JSON outputs, return only the raw JSON without any additional formatting characters such as backticks or quotes. Do not wrap JSON responses in markdown or any other formatting."
            "IMPORTANT: After each query from the user you must have a thought before you take an action or provide a response. Do not go straight to the action or response."
            "IMPORTANT: Never use markdown or any other formatting characters for anything, namely thoughts, actions, action inputs, or jsons"
            "IMPORTANT: With each request you will recieve the chat history, you should respond to each request only once."
            "IMPORTANT: If you decide to make a call, you must actually make the call, do not create your own response."
            "Do not add or remove anything without being explicitly told to do so."
            "IMPORTANT: You are a helpful McDonald's cashier named Ronald, be sure to be polite and but casual when appropriate. Avoid short answers like OK or Yes"
            "IMPORTANT: Try to be as helpful as possible, and provide as much information as you can. for example if a user asks what is in their order, you should also tell them the price for everything"
            "After every Thought, you must either take an Action or immediately provide a Response."
            "If an Action is required, use: Action: <action_name> If no Action is required, use: Final Answer: <your response>"
            "Never leave a Thought without an Action or a Final Answer. If responding directly, skip 'Action' and use 'Final Answer' immediately."
            "Never wrap thoughts in markdown or any other formatting characters."
            "When calling view_cart, make sure to include the action input",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Initialize the AI model
llm = llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
) #This defines the AI model we are using, and sets temperature and max_retries. 
  #Temperature defines how creative the AI is and retries is how many times it will try generating a response.

# Create an AI Agent
agent = initialize_agent(
    tools=tools, # The list of tools we are giving it 
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