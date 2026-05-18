import serpapi
import os
import json
client = serpapi.Client(api_key=os.getenv("SERPAPIKEY"))
results = client.search({
  "engine": "google_flights",
  "departure_id": "DXB",
  "arrival_id": "CAI",
  "currency": "USD",
  "type": "2",
  "outbound_date": "2026-05-20"
})

print(json.dumps(results["best_flights"], indent=2))
