import json
import time
import pandas as pd
from curl_cffi import requests

MILANO_AIRPORTS = ["MXP", "LIN", "BGY"]

# Header avanzati per superare i controlli Cloudflare ed evitare risposte vuote
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
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

# Creiamo una sessione persistente per mantenere i cookie di verifica Cloudflare
session = requests.Session()

try:
    # 1. Passo di riscaldamento: richiediamo l'homepage per acquisire i cookie di sessione
    print("Visita iniziale homepage per inizializzare i cookie di sessione...")
    session.get("https://www.flightsfrom.com/", impersonate="chrome124", headers=headers, timeout=15)
    time.sleep(2)
except Exception as e:
    print(f"Avviso riscaldamento: {e}")

for origin_iata in MILANO_AIRPORTS:
    print(f"\nRecupero dati per {origin_iata}...")
    extracted_flag = False
    
    try:
        url = f"https://www.flightsfrom.com/{origin_iata}/destinations"
        headers["Referer"] = "https://www.flightsfrom.com/"
        
        res = session.get(
            url,
            impersonate="chrome124",
            headers=headers,
            timeout=20
        )
        
        if res.status_code == 200:
            html = res.text
            
            # Verifichiamo la presenza del blocco dati
            if "var metadata = " in html:
                json_part = html.split("var metadata = ")[1].split(";</script>")[0]
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
                extracted_flag = True
            else:
                print(f"-> Cloudflare o pagina non standard rilevata (lunghezza HTML: {len(html)} caratteri).")
        else:
            print(f"-> Errore HTTP: {res.status_code}")
            
    except Exception as e:
        print(f"-> Errore durante l'estrazione da {origin_iata}: {e}")
        
    time.sleep(3)

print(f"\nScraping completato. Righe estratte totali: {len(rows)}")

cols = ["OriginIATA", "DestinationIATA", "Airport", "Airline", "VisitedWeekdays", "Voli_Sett", "Aircraft", "Duration", "Seasonality"]
df = pd.DataFrame(rows if rows else [], columns=cols)
df.to_csv("rotte_complete.csv", index=False)

if len(rows) > 0:
    print("SUCCESS: File rotte_complete.csv salvato con successo e popolato di dati!")
else:
    print("ERRORE: Nessun dato estratto. Controlla i log di GitHub Actions.")
