from fastapi import APIRouter # <-- Import APIRouter instead of FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.agent.graph import app_graph 

# Initialize a router, not a full app
router = APIRouter() 
sessions = {} # In memory session

class ChatRequest(BaseModel):
    session_id: str
    answers: dict
    message: str

# Use @router instead of @app
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Check if the session is already stored in sessions, if not create one
    if request.session_id not in sessions:
        sessions[request.session_id] = {"messages": []} 

    current_state = sessions[request.session_id]

    structured_prompt = f""" 
        User selected these options from the UI:
        Budget: {request.answers.get('budget')}
        use case: {request.answers.get('use_case')}
        Priority: {request.answers.get('priority')}
        Transmission: {request.answers.get('transmission')}

        Additional user note: {request.message}
        """

    # Add this to message state
    current_state["messages"].append(HumanMessage(content=structured_prompt))

    # Push the state to the agent
    final_state = app_graph.invoke(current_state)

    # Save updated state
    sessions[request.session_id] = final_state 

    # If Node 2 asks for clarity
    if final_state.get("needs_clarification") == True:
        return {
            "type": "clarification",
            "data": {
                "question": final_state["clarification_question"]
            }       
        }
    
    # If no doubts, return JSON to frontend
    else: 
        return {
            "type": "recommendation",
            "data": final_state["final_response"]
        }
    
from app.car_loader import CAR_DATASET

@router.get("/cars")
async def get_all_cars():
    return {"data": CAR_DATASET}