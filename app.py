import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re

NASDAQ_API_KEY = "6XC-roD1G-yYTA668Uxy"

def fetch_multpl(symbol):
    url = f"https://data.nasdaq.com/api/v3/datasets/MULTPL/{symbol}.json?api_key={NASDAQ_API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    j = r.json()
    return j["dataset"]["data"][0][1]

def scrape_gurufocus_pe(url):
    r = requests.get(url, headers={'User-Agent': 'PE-Dashboard/1.0'})
    r.raise_for_status()
    m = re.search(r'"Last Value"\s*([0-9]+\.*[0-9]*)', r.text)
    if m:
        return float(m.group(1))
    # fallback text parse
    soup = BeautifulSoup(r.text, "html.parser")
    el = soup.find("h1")
    if el:
        txt = el.get_text()
        num = re.search(r':\s*([0-9]+\.*[0-9]*)', txt)
        if num:
            return float(num.group(1))
    raise ValueError("PE not found")

def fetch_data():
    data = {}
    # CSI 300
    try:
        data["CSI300"] = {"pe": scrape_gurufocus_pe("https://www.gurufocus.com/economic_indicators/4569/pe-ratio-ttm-for-the-csi-300-index")}
    except Exception as e:
        data["CSI300"] = {"pe": None, "error": str(e)}

    # Nasdaq Composite
    try:
        data["Nasdaq"] = {"pe": fetch_multpl("PCOMP_PE_RATIO_MONTH")}
    except Exception as e:
        data["Nasdaq"] = {"pe": None, "error": str(e)}

    # S&P 500
    try:
        data["SP500"] = {"pe": fetch_multpl("SP500_PE_RATIO_MONTH")}
    except Exception as e:
        data["SP500"] = {"pe": None, "error": str(e)}

    # Hang Seng Index
    try:
        data["HSI"] = {"pe": scrape_gurufocus_pe("https://www.gurufocus.com/economic_indicators/5732/pe-ratio-ttm-for-the-hang-seng-index")}
    except Exception as e:
        data["HSI"] = {"pe": None, "error": str(e)}

    data["last_updated"] = datetime.utcnow().isoformat()
    return data

if __name__ == "__main__":
    result = fetch_data()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Updated:", result)
