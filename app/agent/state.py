from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState( TypedDict):
    """
    Global state for the car recommendation agent,
    this dict is passed between nodes
    """

    messages: Annotated[List[BaseMessage], add_messages]
    buyer_profile: Optional[Dict[str, Any]] #node1
    needs_clarification: bool #if ai wants clarity from node.2
    clarification_question: Optional[str]
    search_results: Optional[List[Dict[str,Any]]] # from node 3 top 5 cars
    relaxed_budget: bool = False
    final_response: Optional[Dict[str, Any]]