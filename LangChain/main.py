from langchain_core.messages import HumanMessage
from agent import app

print("\nAI-Powered Shopping Cart")
print("You can ask the AI to add or remove items, and check your cart.")
print("Type 'exit' or 'quit' to stop.\n")

while True:
    user_input = input("Your request: ")
    if user_input.lower() in ["exit", "quit"]:
        print("\nThank you for shopping! Have a great day!")
        break
    try:
        input_messages = [HumanMessage(user_input)]
        output = app.invoke({"messages": input_messages}, {"configurable": {"thread_id": "abc345"}})
        output["messages"][-1].pretty_print()
    except Exception as e:
        print(f"\nError: {str(e)}\n")
