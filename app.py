import requests
import json
from datetime import datetime

# === API 配置 ===
NASDAQ_API_KEY = "D6LJq9S9oorAZ_YVgiQn"

API_CONFIG = {
    "csi300": {
        "url": "https://placeholder.api/csi300",   # 占位符，请换成真实API
        "params": {}
    },
    "nasdaq": {
        "url": f"https://data.nasdaq.com/api/v3/datasets/NASDAQOMX/COMP.json",
        "params": {"api_key": NASDAQ_API_KEY}
    },
    "sp500": {
        "url": "https://placeholder.api/sp500",
        "params": {}
    },
    "hsi": {
        "url": "https://placeholder.api/hsi",
        "params": {}
    }
}

def fetch_data():
    results = {}
    for name, cfg in API_CONFIG.items():
        try:
            res = requests.get(cfg["url"], params=cfg["params"])
            res.raise_for_status()
            data = res.json()

            # 这里只做演示，假设结构为 { dataset: { data: [[date, value], ...] } }
            if name == "nasdaq":
                last_date, last_value = data["dataset"]["data"][0]
            else:
                # 其他API需要你替换
                last_date, last_value = "2025-09-01", 0  

            results[name] = {
                "date": last_date,
                "value": last_value
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    return results

if __name__ == "__main__":
    results = fetch_data()
    results["last_updated"] = datetime.utcnow().isoformat()

    with open("data.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("✅ Data updated:", results)
