import serpapi
import os
import json
import airportsdata
from src.state import TripState
client = serpapi.Client(api_key=os.getenv("SERPAPIKEY"))

airports = airportsdata.load("IATA")
city_to_iata = {}
for code, airport in airports.items():
    city = airport["city"]
    if city not in city_to_iata:
        city_to_iata[city] = code
    elif "International" in airport["name"]:
        city_to_iata[city] = code
def get_iata(city: str) -> str:
    code = city_to_iata.get(city)
    if code is None:
        raise ValueError(f"No IATA code found for city: {city}")
    return code


def flight_node (state: TripState) -> dict: 
    try: 
        departure = state.get("origin")
        departure_code = get_iata(departure)
        arrival =  state.get("destination")
        arrival_code = get_iata(arrival)
        currency = state.get("currency")
        dates = state.get("dates")
        out_date = dates.get("start")
        return_date = dates.get("end")

        results = client.search({
        "engine": "google_flights",
        "departure_id": departure_code,
        "arrival_id": arrival_code,
        "currency": currency,
        "type": "1",
        "outbound_date": out_date,
        "return_date": return_date
        })
        return {"flights": results["best_flights"]}
    except Exception as e:
        return {"errors": {"flight_agent": str(e)}}

