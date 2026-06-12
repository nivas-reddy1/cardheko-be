from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import AgentState 
from app.agent.tools import search_cars_tool
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, api_key = API_KEY)

# 1. Define the schema for the extracted profile
class BuyerProfile(BaseModel):
    """Structured profile containing extracted car buyer preferences."""
    budget: Optional[int] = Field(
        None, description="The maximum budget specified by the buyer in numbers (e.g., 2500000)."
    )
    use_case: Optional[str] = Field(
        None, description="Primary use case, e.g., daily commute, family trips, off-roading, track days."
    )
    priority: Optional[str] = Field(
        None, description="Main priority, e.g., mileage/fuel efficiency, safety, performance, comfort, tech features."
    )
    transmission: Optional[str] = Field(
        None, description="Preferred transmission type: Automatic, Manual, or No Preference."
    )
    seating_capacity: Optional[int] = Field(
        None, description="Preferred number of seats (e.g., 5-seater, 7-seater) extracted from user text if mentioned."
    )
    fuel_type: Optional[str] = Field(
        None, description="Preferred fuel type: Petrol, Diesel, Electric (EV), Hybrid, if mentioned."
    )


structured_llm = llm.with_structured_output(BuyerProfile)

extraction_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert data extraction assistant for a car recommendation system. "
        "Analyze the conversation history and extract the buyer's preferences into the required structured format. "
        "If a preference is missing or ambiguous, leave it as null. Do not guess values unless explicitly stated or strongly implied."
    ),
    ("placeholder", "{messages}"),
])

extraction_chain = extraction_prompt | structured_llm

#node 1
def extract_profile_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Parses the conversation history and extracts structured buyer preferences.
    Updates the 'buyer_profile' in the global state.
    """
    # Extraction
    extracted_profile = extraction_chain.invoke({"messages": state["messages"]})
    
    return {
        "buyer_profile": extracted_profile.model_dump()
    }


#Node2
def check_requirements_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Evaluates the buyer_profile to ensure essential fields are present.
    If fields are missing, it formulates a question to send back to the frontend.
    """
    # Safely get the profile, default to empty dict if missing
    profile = state.get("buyer_profile") or {}
    
    missing_fields = []
    
    if not profile.get("budget"):
        missing_fields.append("maximum budget")
    if not profile.get("use_case"):
        missing_fields.append("primary use case (e.g., daily commute, family trips)")
        
    if missing_fields:
        fields_str = " and ".join(missing_fields)
        question = f"I'd love to find the perfect car for you! To narrow down the best options, could you please let me know your {fields_str}?"
        
        return {
            "needs_clarification": True,
            "clarification_question": question
        }
    #if proced, state foes to node3
    return {
        "needs_clarification": False,
        "clarification_question": None
    }

#node3
def search_database_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: Uses extracted buyer profile to search the car database.
    Falls back to relaxing the budget by 10% if no results are found.
    """
    profile = state.get("buyer_profile") or {}
 
    budget = profile.get("budget")
    transmission = profile.get("transmission")
    use_case = profile.get("use_case")
 
    # Initial strict search
    cars_found = search_cars_tool.invoke(
        {
            "budget": budget,
            "transmission": transmission,
            "use_case": use_case,
        }
    )
 
    relaxed_budget_triggered = False
 
    # Fallback — relax budget by 10% if nothing found
    if not cars_found and budget is not None:
        relaxed_budget = int(budget * 1.10)
        relaxed_budget_triggered = True
 
        cars_found = search_cars_tool.invoke(
            {
                "budget": relaxed_budget,
                "transmission": transmission,
                "use_case": use_case,
            }
        )
 
    return {
        "search_results": cars_found,
        "relaxed_budget": relaxed_budget_triggered,
    }


#node4

class CarTradeOff(BaseModel):
    make: str = Field(description="Brand of the car.")
    model: str = Field(description="Model of the car.")
    variant: str = Field(description="Specific variant of the car.")
    price_lakh: float = Field(description="Price in lakhs.")
    why_it_fits: str = Field(
        description="1-2 sentence explanation of why this fits the user's profile."
    )
    trade_off: str = Field(
        description="One honest trade-off for choosing this car."
    )
    image: str = Field(description="Image path from the database.")

class FinalRecommendationResponse(BaseModel):
    summary: str = Field(
        description="Brief friendly opening summarising the user's request and results."
    )
    recommendations: List[CarTradeOff] = Field(
        description="Ranked list of recommended cars with trade-offs."
    )

tradeoff_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert automotive advisor for the Indian car market. "
            "Analyze the buyer profile and the retrieved cars. "
            "For each car explain exactly why it fits their needs using specific data points. "
            "Highlight one honest trade-off per car based on the data. "
            "If relaxed_budget is true, mention in the summary that you slightly expanded their budget.",
        ),
        (
            "human",
            "User Profile: {buyer_profile}\n"
            "Relaxed Budget Triggered: {relaxed_budget}\n"
            "Retrieved Cars: {search_results}",
        ),
    ]
)

formatting_chain = tradeoff_prompt | llm.with_structured_output(
    FinalRecommendationResponse
)

def format_recommendation_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Analyses search results against buyer profile and generates
    the final structured JSON response for the frontend.
    """
    if not state.get("search_results"):
        return {
            "final_response": {
                "summary": (
                    "I couldn't find cars matching those exact requirements. "
                    "Could we try adjusting the budget or transmission preference?"
                ),
                "recommendations": [],
            }
        }
 
    final_output = formatting_chain.invoke(
        {
            "buyer_profile": state.get("buyer_profile"),
            "relaxed_budget": state.get("relaxed_budget"),
            "search_results": state.get("search_results"),
        }
    )
 
    return {"final_response": final_output.model_dump()}