import json
import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

MILANO_AIRPORTS = ["MXP", "LIN", "BGY"]
rows = []

print("Inizializzazione Undetected-Chromedriver...")

# Configurazione delle opzioni per Chrome in ambiente headless (GitHub Actions)
options = uc.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# Avvio del browser stealth
driver = uc.Chrome(options=options)

try:
    for origin_iata in MILANO_AIRPORTS:
        url = f"https://www.flightsfrom.com/{origin_iata}/destinations"
        print(f"\nCaricamento pagina per {origin_iata}: {url}")
        
        driver.get(url)
        
        # Pausa di sicurezza per far completare i controlli Cloudflare e il caricamento JS
        time.sleep(5)
        
        # Estrazione diretta dell'oggetto JavaScript 'metadata' presente nella pagina
        metadata_json = driver.execute_script("return window.metadata ? JSON.stringify(window.metadata) : null;")
        
        if metadata_json:
            data = json.loads(metadata_json)
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
            print(f" -> SUCCESS: Estratte {len(routes)} destinazioni da {origin_iata}")
        else:
            print(f" -> WARNING: window.metadata non trovato per {origin_iata}. Verifica il sorgente pagina.")

finally:
    driver.quit()

print(f"\nScraping completato! Totale rotte estratte: {len(rows)}")

# Generazione file CSV finale
cols = ["OriginIATA", "DestinationIATA", "Airport", "Airline", "VisitedWeekdays", "Voli_Sett", "Aircraft", "Duration", "Seasonality"]
df = pd.DataFrame(rows if rows else [], columns=cols)
df.to_csv("rotte_complete.csv", index=False)

if len(rows) > 0:
    print("SUCCESS: File rotte_complete.csv salvato con dati validi!")
else:
    print("ERRORE: Nessuna riga estratta.")
