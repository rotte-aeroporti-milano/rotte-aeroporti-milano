import json
import time
import pandas as pd
from curl_cffi import requests

headers = {
    "Accept": "application/json",
    "Origin": "https://www.flightsfrom.com",
    "Referer": "https://www.flightsfrom.com/"
}

# 1. Recupera tutti gli aeroporti mondiali
r = requests.get("https://www.flightsfrom.com/airports", impersonate="chrome", headers=headers)
airports_data = r.json()["response"]["airports"]

rows = []

# Nota: per estrarre solo da specifici aeroporti, puoi filtrare qui la lista 'airports_data'
for ap in airports_data:
    origin_iata = ap["IATA"]
    
    try:
        res = requests.get(
            f"https://www.flightsfrom.com/{origin_iata}/destinations",
            impersonate="chrome",
            headers={"Accept": "text/html", "Referer": "https://www.flightsfrom.com/"}
        )
        
        html_content = res.text
        start_str = "var metadata = "
        if start_str in html_content:
            json_str = html_content.split(start_str)[1].split(";")[0]
            data = json.loads(json_str)
            
            for route in data.get("routes", []):
                dest_iata = route.get("iata_to")
                dest_airport_name = route.get("airport_to", {}).get("name", "")
                duration_min = route.get("common_duration")
                
                for aroute in route.get("airlineroutes", []):
                    airline_name = aroute.get("airline", {}).get("name")
                    weekdays = aroute.get("days", "")          # es: 1,3,5
                    frequency = aroute.get("frequency", "")     # Voli/sett
                    aircraft = aroute.get("aircraft", "")       # Modello aereo
                    seasonality = aroute.get("seasonal", "")    # Stagionalità
                    
                    rows.append({
                        "OriginIATA": origin_iata,
                        "DestinationIATA": dest_iata,
                        "Airport": dest_airport_name,
                        "Airline": airline_name,
                        "VisitedWeekdays": weekdays,
                        "Voli_Sett": frequency,
                        "Aircraft": aircraft,
                        "Duration": duration_min,
                        "Seasonality": seasonality
                    })
                    
        time.sleep(0.3) # Pausa di rispetto server
    except Exception as e:
        continue

# 2. Salva il file CSV
df = pd.DataFrame(rows)
df.to_csv("rotte_complete.csv", index=False)
