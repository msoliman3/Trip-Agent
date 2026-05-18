from langgraph.graph import StateGraph, END
from src.state import TripState
from src.retrieval.retriever import rag_node 
from src.agents.flight_agent import flight_node

# placeholder nodes for agents not built yet
def orchestrator_node(state: TripState) -> dict:
    return {}

def hotel_node(state: TripState) -> dict:
    return {}

def weather_node(state: TripState) -> dict:
    return {}

def itinerary_node(state: TripState) -> dict:
    return {}

def budget_node(state: TripState) -> dict:
    return {}

# 1. create the graph with your state type
graph = StateGraph(TripState)

# 2. add nodes
graph.add_node("orchestrator", orchestrator_node)
graph.add_node("flight_node", flight_node)
graph.add_node("hotel_node", hotel_node)
graph.add_node("weather_node", weather_node)
graph.add_node("rag_node", rag_node)
graph.add_node("itinerary_generator", itinerary_node)
graph.add_node("budget_checker", budget_node)


# 3. define the flow
graph.set_entry_point("orchestrator")
graph.add_edge("orchestrator", "flight_node")
graph.add_edge("orchestrator", "hotel_node")
graph.add_edge("orchestrator", "weather_node")
graph.add_edge("orchestrator", "rag_node")
graph.add_edge(["flight_node", "hotel_node", "weather_node", "rag_node"], "itinerary_generator")
graph.add_edge("itinerary_generator", "budget_checker")
graph.add_edge("budget_checker", END)


# 4. compile and run
app = graph.compile()

mytrip = TripState(
    origin="DXB",
    destination="CAI",
    dates={"start": "2026-07-10", "end": "2026-07-30"},
    budget=2000,
    currency="USD",
    interests=["Nature", "Beaches", "Museums"],
    flights=None,
    hotels=None,
    weather=None,
    destination_context=None,
    itinerary=None,
    errors=None,
    is_over_budget=None,
    budget_breakdown=None
)


result = app.invoke(mytrip)
print(result)