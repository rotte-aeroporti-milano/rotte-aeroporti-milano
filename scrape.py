import json
import time
import pandas as pd
from curl_cffi import requests

# Gli aeroporti che ti interessano
MILANO_AIRPORTS = ["MXP", "LIN", "BGY"]

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

rows = []
print("Inizio estrazione voli diretti da Milano (MXP, LIN, BGY)...")

for origin_iata in MILANO_AIRPORTS:
    try:
        url = f"https://www.flightsfrom.com/{origin_iata}/destinations"
        print(f"Richiesta dati per {origin_iata}...")
        
        res = requests.get(
            url,
            impersonate="chrome124",
            headers=headers,
            timeout=15
        )
        
        if res.status_code == 200:
            html_content = res.text
            start_str = "var metadata = "
            
            if start_str in html_content:
                json_str = html_content.split(start_str)[1].split(";</script>")[0]
                data = json.loads(json_str)
                
                # Estrazione dati rotte
                for route in data.get("routes", []):
                    dest_iata = route.get("iata_to")
                    dest_airport_name = route.get("airport_to", {}).get("name", "")
                    duration_min = route.get("common_duration")
                    
                    for aroute in route.get("airlineroutes", []):
                        airline_name = aroute.get("airline", {}).get("name")
                        weekdays = aroute.get("days", "")
                        frequency = aroute.get("frequency", "")
                        aircraft = aroute.get("aircraft", "")
                        seasonality = aroute.get("seasonal", "")
                        
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
                print(f" -> OK: Estratte rotte per {origin_iata}")
            else:
                print(f" -> ATTENZIONE: Blocco metadata non trovato per {origin_iata}")
        else:
            print(f" -> ERRORE: Status code {res.status_code} su {origin_iata}")
            
        time.sleep(1.5)
        
    except Exception as e:
        print(f" -> ERRORE CRITICO su {origin_iata}: {e}")

print(f"\nScraping completato! Totale rotte dirette trovate: {len(rows)}")

# Generazione file CSV finale
if rows:
    df = pd.DataFrame(rows)
    df.to_csv("rotte_complete.csv", index=False)
    print("File rotte_complete.csv creato con successo!")
else:
    print("Nessun dato estratto. Genero una struttura di sicurezza vuota.")
    cols = ["OriginIATA", "DestinationIATA", "Airport", "Airline", "VisitedWeekdays", "Voli_Sett", "Aircraft", "Duration", "Seasonality"]
    pd.DataFrame(columns=cols).to_csv("rotte_complete.csv", index=False)
