import json
import time
import pandas as pd
from curl_cffi import requests

MILANO_AIRPORTS = ["MXP", "LIN", "BGY"]

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.flightsfrom.com/",
    "Origin": "https://www.flightsfrom.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

rows = []
print("Inizio estrazione voli diretti da Milano (MXP, LIN, BGY)...")

for origin_iata in MILANO_AIRPORTS:
    print(f"\n--- Elaborazione {origin_iata} ---")
    extracted = False
    
    # Tentativo 1: Chiamata HTML con estrazione metadata (metodo principale)
    try:
        url_html = f"https://www.flightsfrom.com/{origin_iata}/destinations"
        res = requests.get(url_html, impersonate="chrome124", headers=headers, timeout=15)
        
        if res.status_code == 200 and "var metadata = " in res.text:
            json_str = res.text.split("var metadata = ")[1].split(";</script>")[0]
            data = json.loads(json_str)
            routes = data.get("routes", [])
            
            for route in routes:
                dest_iata = route.get("iata_to")
                dest_airport_name = route.get("airport_to", {}).get("name", "")
                duration_min = route.get("common_duration")
                
                for aroute in route.get("airlineroutes", []):
                    rows.append({
                        "OriginIATA": origin_iata,
                        "DestinationIATA": dest_iata,
                        "Airport": dest_airport_name,
                        "Airline": aroute.get("airline", {}).get("name", ""),
                        "VisitedWeekdays": aroute.get("days", ""),
                        "Voli_Sett": aroute.get("frequency", ""),
                        "Aircraft": aroute.get("aircraft", ""),
                        "Duration": duration_min,
                        "Seasonality": aroute.get("seasonal", "")
                    })
            print(f"-> OK (via HTML): Estratte {len(routes)} destinazioni per {origin_iata}")
            extracted = True
        else:
            print(f"-> HTML non valido o bloccato da Cloudflare (Status: {res.status_code}). Tentativo via API...")
    except Exception as e:
        print(f"-> Errore HTML per {origin_iata}: {e}")

    # Tentativo 2 (Fallback): Endpoint API JSON diretto
    if not extracted:
        try:
            url_api = f"https://www.flightsfrom.com/api/airport/getAirportDetails/{origin_iata}"
            res_api = requests.get(url_api, impersonate="chrome124", headers=headers, timeout=15)
            
            if res_api.status_code == 200:
                data_api = res_api.json()
                routes = data_api.get("response", {}).get("routes", [])
                
                for route in routes:
                    dest_iata = route.get("iata_to")
                    dest_airport_name = route.get("airport_to", {}).get("name", "")
                    duration_min = route.get("common_duration")
                    
                    for aroute in route.get("airlineroutes", []):
                        rows.append({
                            "OriginIATA": origin_iata,
                            "DestinationIATA": dest_iata,
                            "Airport": dest_airport_name,
                            "Airline": aroute.get("airline", {}).get("name", ""),
                            "VisitedWeekdays": aroute.get("days", ""),
                            "Voli_Sett": aroute.get("frequency", ""),
                            "Aircraft": aroute.get("aircraft", ""),
                            "Duration": duration_min,
                            "Seasonality": aroute.get("seasonal", "")
                        })
                print(f"-> OK (via API): Estratte {len(routes)} destinazioni per {origin_iata}")
            else:
                print(f"-> API Error {res_api.status_code} per {origin_iata}")
        except Exception as e_api:
            print(f"-> Errore API per {origin_iata}: {e_api}")

    time.sleep(2)

print(f"\nScraping completato! Totale righe create: {len(rows)}")

cols = ["OriginIATA", "DestinationIATA", "Airport", "Airline", "VisitedWeekdays", "Voli_Sett", "Aircraft", "Duration", "Seasonality"]
if rows:
    df = pd.DataFrame(rows)
    df.to_csv("rotte_complete.csv", index=False)
    print("-> Archivo rotte_complete.csv salvato con successo!")
else:
    print("-> ERRORE: Nessuna riga estratta da nessun aeroporto.")
    pd.DataFrame(columns=cols).to_csv("rotte_complete.csv", index=False)
