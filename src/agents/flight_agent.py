import serpapi
import os
import json
from src.state import TripState
client = serpapi.Client(api_key=os.getenv("SERPAPIKEY"))



def flight_node (state: TripState) -> dict: 
    try: 
        departure = state.get("origin")
        arrival =  state.get("destination")
        currency = state.get("currency")
        dates = state.get("dates")
        out_date = dates.get("start")
        return_date = dates.get("end")

        results = client.search({
        "engine": "google_flights",
        "departure_id": departure,
        "arrival_id": arrival,
        "currency": currency,
        "type": "1",
        "outbound_date": out_date,
        "return_date": return_date
        })
        return {"flights": results["best_flights"]}
    except Exception as e:
        return {"errors": {"flight_agent": str(e)}}

