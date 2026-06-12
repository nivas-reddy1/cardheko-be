from langgraph.graph import StateGraph, END
from app.agent.state import AgentState 
from app.agent.nodes import ( check_requirements_node, extract_profile_node, format_recommendation_node, search_database_node)

def route_after_check(state: AgentState) -> str:
    """Reads the state and returns the name of the next node."""
    if state.get("needs_clarification"):
        return "end_execution" 
    return "search_database"   


workflow = StateGraph(AgentState)


workflow.add_node("extract_profile", extract_profile_node) # Node 1
workflow.add_node("check_requirements", check_requirements_node) # Node 2
workflow.add_node("search_database", search_database_node)        # Node 3
workflow.add_node("format_recommendation", format_recommendation_node)  # Node 4


workflow.set_entry_point("extract_profile")
workflow.add_edge("extract_profile", "check_requirements")


workflow.add_conditional_edges(
    "check_requirements", 
    route_after_check,
    {
        "end_execution": END,          
        "search_database": "search_database" # Continues to Node 3
    }
)

workflow.add_edge("search_database", "format_recommendation")  # Node 3 → Node 4
workflow.add_edge("format_recommendation", END) 

app_graph = workflow.compile()