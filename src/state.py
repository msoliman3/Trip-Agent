from typing import TypedDict, Optional

class TripState(TypedDict):
    # Input
    origin: str 
    destination: str
    dates: dict # {"start": "2026-05-17", "end": "2026-05-24"}
    budget: float
    currency: str
    interests: list[str]
    
    # Each agent writes its results here
    flights: Optional[list]
    hotels: Optional[list]
    weather: Optional[dict]
    destination_context: Optional[str]
    budget_breakdown: Optional[dict]
    is_over_budget: Optional[bool]

    errors: Optional[dict[str, str]]
    
    # Final output
    itinerary: Optional[str]