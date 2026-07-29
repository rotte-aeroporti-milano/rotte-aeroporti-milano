import json
import time
import subprocess
import pandas as pd
import undetected_chromedriver as uc

MILANO_AIRPORTS = ["MXP", "LIN", "BGY"]
rows = []

print("Inizializzazione Undetected-Chromedriver...")

# Rileviamo la versione principale di Chrome installata per evitare mismatch con ChromeDriver
chrome_version = None
try:
    version_output = subprocess.check_output(["google-chrome", "--version"]).decode("utf-8")
    # Estraiamo la versione principale (es. "150" da "Google Chrome 150.0.7871.186")
    chrome_version = int(version_output.strip().split(" ")[2].split(".")[0])
    print(f"Versione di Chrome rilevata sul sistema: {chrome_version}")
except Exception as e:
    print(f"Impossibile rilevare la versione esatta di Chrome, uso fallback automatico: {e}")

options = uc.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# Passiamo version_main per allineare perfettamente ChromeDriver al browser
if chrome_version:
    driver = uc.Chrome(options=options, version_main=chrome_version, use_subprocess=True)
else:
    driver = uc.Chrome(options=options, use_subprocess=True)

try:
    for origin_iata in MILANO_AIRPORTS:
        url = f"https://www.flightsfrom.com/{origin_iata}/destinations"
        print(f"\nCaricamento pagina per {origin_iata}: {url}")
        
        driver.get(url)
        time.sleep(6)  # Pausa di sicurezza per il bypass Cloudflare
        
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
            print(f" -> WARNING: window.metadata non trovato per {origin_iata}")

finally:
    driver.quit()

print(f"\nScraping completato! Totale rotte estratte: {len(rows)}")

cols = ["OriginIATA", "DestinationIATA", "Airport", "Airline", "VisitedWeekdays", "Voli_Sett", "Aircraft", "Duration", "Seasonality"]
df = pd.DataFrame(rows if rows else [], columns=cols)
df.to_csv("rotte_complete.csv", index=False)
print("File rotte_complete.csv salvato con successo!")
