from langchain_core.messages import HumanMessage
from agent import app
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

fastapi_app = FastAPI()

# Allows for Javascript code with a different origin to communicate with server
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    message: str

@fastapi_app.post("/chat")
def chat(request: UserRequest):
    try:
        user_input = request.message
        if not user_input:
            raise HTTPException(status_code=400, detail="No message provided")
    
        input_messages = [HumanMessage(user_input)]
        output = app.invoke({"messages": input_messages}, {"configurable": {"thread_id": "abc345"},"response_format": "json"},)
        return {"content": output["messages"][-1].content}
    except Exception as e:
        return {"error": "Something went wrong while processing your message. Please try again later."}

if __name__ == "__main__":

    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)