import json
import time
import pandas as pd
from curl_cffi import requests

MILANO_AIRPORTS = ["MXP", "LIN", "BGY"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

rows = []
print("Inizio estrazione voli diretti tramite Proxy per bypassare il blocco 403...")

for origin_iata in MILANO_AIRPORTS:
    print(f"\nRecupero dati per {origin_iata}...")
    try:
        # Utilizzo di un proxy CORS aperto per mascherare l'IP di GitHub Actions
        target_url = f"https://www.flightsfrom.com/{origin_iata}/destinations"
        proxy_url = f"https://api.allorigins.win/get?url={target_url}"
        
        res = requests.get(proxy_url, timeout=20)
        
        if res.status_code == 200:
            contents = res.json().get("contents", "")
            
            if "var metadata = " in contents:
                json_part = contents.split("var metadata = ")[1].split(";</script>")[0]
                data = json.loads(json_part)
                routes = data.get("routes", [])
                
                for route in routes:
                    dest_iata = route.get("iata_to")
                    dest_name = route.get("airport_to", {}).get("name", "")
                    duration = route.get("common_duration")
                    
                    for aroute in route.get("airlineroutes", []):
                        rows.append({
                            "OriginIATA": origin_iata,
                            "DestinationIATA": dest_iata,
                            "Airport": dest_name,
                            "Airline": aroute.get("airline", {}).get("name", ""),
                            "VisitedWeekdays": aroute.get("days", ""),
                            "Voli_Sett": aroute.get("frequency", ""),
                            "Aircraft": aroute.get("aircraft", ""),
                            "Duration": duration,
                            "Seasonality": aroute.get("seasonal", "")
                        })
                print(f"-> Riuscito: Estratte {len(routes)} destinazioni per {origin_iata}")
            else:
                print(f"-> Errore: Blocco metadata non trovato nella risposta del proxy.")
        else:
            print(f"-> Errore Proxy HTTP: {res.status_code}")
            
    except Exception as e:
        print(f"-> Errore su {origin_iata}: {e}")
        
    time.sleep(2)

print(f"\nScraping completato. Righe estratte totali: {len(rows)}")

cols = ["OriginIATA", "DestinationIATA", "Airport", "Airline", "VisitedWeekdays", "Voli_Sett", "Aircraft", "Duration", "Seasonality"]
df = pd.DataFrame(rows if rows else [], columns=cols)
df.to_csv("rotte_complete.csv", index=False)
