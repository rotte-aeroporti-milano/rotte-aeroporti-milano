import json
import time
import pandas as pd
from curl_cffi import requests

headers = {
    "Accept": "application/json",
    "Origin": "https://www.flightsfrom.com",
    "Referer": "https://www.flightsfrom.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

rows = []

try:
    print("Recupero elenco aeroporti...")
    r = requests.get("https://www.flightsfrom.com/airports", impersonate="chrome", headers=headers, timeout=15)
    
    if r.status_code != 200:
        print(f"Errore nella richiesta iniziale aeroporti: Status {r.status_code}")
        exit(1)
        
    airports_data = r.json().get("response", {}).get("airports", [])
    print(f"Trovati {len(airports_data)} aeroporti.")

    # NOTA: Per un test iniziale veloce puoi provare con un sottoinsieme: airports_data[:20]
    for ap in airports_data:
        origin_iata = ap.get("IATA")
        if not origin_iata:
            continue
            
        try:
            res = requests.get(
                f"https://www.flightsfrom.com/{origin_iata}/destinations",
                impersonate="chrome",
                headers={"Accept": "text/html", "Referer": "https://www.flightsfrom.com/"},
                timeout=10
            )
            
            if res.status_code == 200:
                html_content = res.text
                start_str = "var metadata = "
                if start_str in html_content:
                    json_str = html_content.split(start_str)[1].split(";</script>")[0]
                    data = json.loads(json_str)
                    
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
            time.sleep(0.5)  # Pausa precauzionale per evitare blocchi IP
        except Exception as e:
            print(f"Errore durante lo scraping dell'aeroporto {origin_iata}: {e}")
            continue

    if rows:
        df = pd.DataFrame(rows)
        df.to_csv("rotte_complete.csv", index=False)
        print(f"File rotte_complete.csv generato con successo con {len(rows)} righe!")
    else:
        print("Nessun dato estratto. Generazione CSV annullata.")
        exit(1)

except Exception as global_e:
    print(f"Errore critico nello script: {global_e}")
    exit(1)
