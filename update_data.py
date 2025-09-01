
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PE Dashboard Updater
- Fetches/refreshes 10-year TTM P/E time series for: S&P 500, CSI 300, Hang Seng Index, Nasdaq Composite
- Writes CSVs under ./data and renders a static ECharts dashboard under ./site

Important:
- S&P 500: uses Nasdaq Data Link (MULTPL datasets). Set NASDAQ_API_KEY in env.
- CSI 300: uses AkShare to pull CSIndex valuation (市盈率TTM).
- HSI: tries Hang Seng Indexes valuation JSON (if reachable), else tries GuruFocus econ indicator page scrape (may require cookies/login).
- NASDAQ Composite: No stable free API; function provided to plug your own CSV URL or use GuruFocus if available.
"""
import os
import io
import re
import json
import time
import math
import csv
import datetime as dt
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

CONFIG = json.load(open("config.json", "r", encoding="utf-8"))
DATA_DIR = CONFIG["output"]["data_dir"]
SITE_DIR = CONFIG["output"]["site_dir"]
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SITE_DIR, exist_ok=True)

def to_date(x):
    if pd.isna(x): return None
    if isinstance(x, (pd.Timestamp, dt.date, dt.datetime)): return pd.to_datetime(x).date()
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def last_n_years(df: pd.DataFrame, n=10, date_col="date"):
    if df.empty: return df
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    cutoff = pd.Timestamp.today().normalize() - pd.DateOffset(years=n)
    return df[df[date_col] >= cutoff].sort_values(date_col)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def http_get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", "PE-Dashboard/1.0 (+https://example.com)")
    resp = requests.get(url, headers=headers, timeout=20, **kwargs)
    resp.raise_for_status()
    return resp

def save_csv(df: pd.DataFrame, path: str):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"Wrote {path}  rows={len(df)}")

# ---------- Loaders ----------

def sp500_from_nasdaq_datalink(api_key: Optional[str] = None) -> pd.DataFrame:
    """
    MULTPL/SP500_PE_RATIO_DAILY (preferred) or MULTPL/SP500_PE_RATIO_MONTH fallback
    Columns usually: Date, Value
    """
    api_key = api_key or os.getenv("NASDAQ_API_KEY")
    if not api_key:
        raise RuntimeError("Set NASDAQ_API_KEY env for S&P 500 loader.")
    def fetch(dataset):
        url = f"https://data.nasdaq.com/api/v3/datasets/{dataset}.csv"
        params = {"api_key": api_key}
        r = http_get(url, params=params)
        df = pd.read_csv(io.StringIO(r.text))
        # Normalize
        date_col = [c for c in df.columns if c.lower().startswith("date")][0]
        value_col = [c for c in df.columns if c.lower() in ("value","pe_ratio","ratio")][0]
        return df.rename(columns={date_col:"date", value_col:"pe"})
    try:
        df = fetch(CONFIG["indices"]["SP500"]["datalink_dataset_daily"])
    except Exception:
        df = fetch(CONFIG["indices"]["SP500"]["datalink_dataset_monthly"])
    df = df[["date","pe"]].dropna()
    return last_n_years(df, n=10)

def csi300_from_csindex_via_akshare() -> pd.DataFrame:
    """
    Uses AkShare to download CSIndex valuation table and extract 市盈率(TTM). Daily frequency.
    """
    import akshare as ak
    code = CONFIG["indices"]["CSI300"]["csindex_code"]
    # ak.stock_zh_index_value_csindex(symbol="000300")
    df = ak.stock_zh_index_value_csindex(symbol=code)
    # Expected columns: ['日期','市盈率1','市盈率2','市盈率TTM','市净率','股息率']
    # Standardize to date & pe (TTM)
    # Some ak versions label 市盈率(TTM) slightly differently, try fuzzy match
    pe_col = None
    for c in df.columns:
        if "TTM" in str(c) and "市盈" in str(c):
            pe_col = c; break
    if pe_col is None:
        # fallback to a typical column name
        pe_col = "市盈率TTM"
    out = df.rename(columns={"日期":"date", pe_col:"pe"})[["date","pe"]]
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out = out.dropna().sort_values("date")
    return last_n_years(out, n=10)

def hsi_from_hkex_or_gurufocus() -> pd.DataFrame:
    """
    Strategy A: Use Hang Seng Indexes valuation JSON that powers hsi.com.hk charts (if reachable).
    Strategy B: Scrape GuruFocus 'PE Ratio (TTM) for the Hang Seng Index' table (may require cookies).
    Both are best-effort; for production, consider licensed feeds from HSIL/CEIC.
    """
    # Strategy A placeholder (endpoint patterns change often; left as optional)
    try:
        # Example pattern (subject to change): this block is defensive and may fail gracefully
        # If you have a stable JSON endpoint, set HSI_JSON_URL env to override.
        json_url = os.getenv("HSI_JSON_URL")
        if json_url:
            r = http_get(json_url)
            js = r.json()
            # Expect ['data'] list of [timestamp, value]
            if isinstance(js, dict) and "data" in js:
                arr = js["data"]
                df = pd.DataFrame(arr, columns=["ts","pe"])
                df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.date
                out = df[["date","pe"]].dropna()
                return last_n_years(out, 10)
    except Exception as e:
        pass
    # Strategy B: GuruFocus HTML table scrape
    try:
        url = "https://www.gurufocus.com/economic_indicators/5732/pe-ratio-ttm-for-the-hang-seng-index"
        r = http_get(url)
        # Parse simple JSON embedded or table CSV
        # Look for "data": [[date,value],...]
        m = re.search(r'"data"\s*:\s*(\[[^\]]+\])', r.text)
        if m:
            arr = json.loads(m.group(1))
            df = pd.DataFrame(arr, columns=["date","pe"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            return last_n_years(df, 10)
    except Exception:
        pass
    raise RuntimeError("HSI loader could not fetch data automatically; please configure HSI_JSON_URL or a licensed source.")

def nasdaq_composite_from_gurufocus_or_proxy() -> pd.DataFrame:
    """
    There is no stable free Composite TTM P/E feed. Try GuruFocus if available, else allow user-provided CSV.
    To use your own CSV URL with 'date,pe' columns, set NASDAQ_COMP_CSV env.
    """
    # User-provided CSV
    csv_url = os.getenv("NASDAQ_COMP_CSV")
    if csv_url:
        r = http_get(csv_url)
        df = pd.read_csv(io.StringIO(r.text))
        df = df.rename(columns={"Date":"date","DATE":"date","PE":"pe","Pe":"pe","Pe_ttm":"pe"})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return last_n_years(df, 10)
    # Attempt GuruFocus? (No public composite P/E page; likely to fail)
    raise RuntimeError("Nasdaq Composite P/E feed not configured. Set NASDAQ_COMP_CSV to a CSV with columns date,pe.")

LOADER_MAP = {
    "sp500_from_nasdaq_datalink": sp500_from_nasdaq_datalink,
    "csi300_from_csindex_via_akshare": csi300_from_csindex_via_akshare,
    "hsi_from_hkex_or_gurufocus": hsi_from_hkex_or_gurufocus,
    "nasdaq_composite_from_gurufocus_or_proxy": nasdaq_composite_from_gurufocus_or_proxy,
}

def run_one(key: str) -> Optional[pd.DataFrame]:
    meta = CONFIG["indices"][key]
    loader_name = meta["loader"]
    fn = LOADER_MAP[loader_name]
    print(f"Fetching {meta['name']} via {loader_name} ...")
    df = fn()  # may raise
    df = df.sort_values("date")
    save_csv(df, os.path.join(DATA_DIR, f"{key}.csv"))
    return df

def generate_site(dfs: dict):
    # Assemble site/index.html using ECharts and Plotly fallback
    # We will produce ECharts line chart with responsive layout.
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>全球主要指数 10 年市盈率（PE）走势</title>
  <style>
    :root {{
      --bg: #0b0f1a; --card: #111827; --fg: #e5e7eb; --muted: #9ca3af; --accent: #60a5fa;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; background: var(--bg); color: var(--fg);}}
    header {{ padding: 16px 20px; border-bottom: 1px solid #1f2937; }}
    h1 {{ margin: 0 0 6px; font-size: 20px; font-weight: 700;}}
    p.subtitle {{ margin: 0; color: var(--muted); font-size: 13px;}}
    #chart {{ width: 100%; height: 68vh; max-height: 760px; }}
    .footer {{ padding: 14px 20px; color: var(--muted); font-size: 12px; border-top: 1px solid #1f2937;}}
    .legend-note {{ margin-top: 6px; font-size: 12px; color: var(--muted);}}
    @media (max-width: 640px) {{
      #chart {{ height: 60vh; }}
      h1 {{ font-size: 18px; }}
    }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
</head>
<body>
  <header>
    <h1>全球主要指数 · 10年PE（TTM）走势</h1>
    <p class="subtitle">鼠标悬停查看具体日期与市盈率；数据每日北京时间 15:00 自动更新。</p>
  </header>
  <main>
    <div id="chart"></div>
    <div class="legend-note">指数：沪深300 · 标普500 · 恒生指数 · 纳斯达克综合</div>
  </main>
  <div class="footer" id="footer"></div>
  <script>
    async function loadCSV(path) {{
      const res = await fetch(path + "?v=" + Date.now());
      const txt = await res.text();
      const rows = txt.trim().split(/\\n/).slice(1).map(r=>r.split(","));
      return rows.map(r=>({{date:r[0], pe: parseFloat(r[1])}})).filter(x=>!isNaN(x.pe));
    }}
    async function main(){{
      const sp = await loadCSV("../data/SP500.csv");
      const csi = await loadCSV("../data/CSI300.csv");
      const hsi = await loadCSV("../data/HSI.csv").catch(_=>[]);
      const nas = await loadCSV("../data/NASDAQ.csv").catch(_=>[]);
      const series = [
        {{ name: "标普500", data: sp.map(x=>[x.date, x.pe]) }},
        {{ name: "沪深300", data: csi.map(x=>[x.date, x.pe]) }},
      ];
      if (hsi.length) series.push({{ name: "恒生指数", data: hsi.map(x=>[x.date, x.pe]) }});
      if (nas.length) series.push({{ name: "纳斯达克综合", data: nas.map(x=>[x.date, x.pe]) }});

      const dates = [...new Set(series.flatMap(s=>s.data.map(d=>d[0])) )].sort();
      const el = document.getElementById('chart');
      const chart = echarts.init(el, null, {{renderer:'canvas'}});
      const option = {{
        backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg'),
        textStyle: {{ color: getComputedStyle(document.documentElement).getPropertyValue('--fg') }},
        tooltip: {{
          trigger: 'axis',
          axisPointer: {{ type: 'line' }},
          valueFormatter: (v)=> (v!=null? v.toFixed(2): v)
        }},
        legend: {{
          top: 10
        }},
        grid: {{ left: 40, right: 24, top: 50, bottom: 60 }},
        xAxis: {{
          type: 'category', data: dates, boundaryGap: false, axisLabel: {{ formatter: (v)=> v.slice(0,10) }}
        }},
        yAxis: {{
          type: 'value',
          name: 'PE（TTM）',
          nameGap: 18,
          splitLine: {{ show: true }}
        }},
        series: series.map((s)=>({{
          type: 'line',
          name: s.name,
          showSymbol: false,
          smooth: false,
          data: s.data,
        }}))
      }};
      chart.setOption(option);
      window.addEventListener("resize", ()=> chart.resize());
      const sourceNote = `数据来源： 
        标普500：Nasdaq Data Link (MULTPL)；
        沪深300：中证指数（经 AkShare）；
        恒生指数：Hang Seng Indexes / GuruFocus（若显示）；
        纳斯达克综合：用户配置数据源（若显示）。 
        | 更新频率：每个交易日北京时间15:00自动更新`;
      document.getElementById("footer").textContent = sourceNote;
    }}
    main();
  </script>
</body>
</html>
"""
    open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8").write(html)
    print("Wrote site/index.html")

def main():
    failures = []
    dfs = {}
    for key in ["SP500","CSI300","HSI","NASDAQ"]:
        try:
            df = run_one(key)
            dfs[key] = df
        except Exception as e:
            print(f"[WARN] {key} failed: {e}")
            # Create an empty placeholder CSV so the site still loads
            pd.DataFrame({"date":[], "pe":[]}).to_csv(os.path.join(DATA_DIR, f"{key}.csv"), index=False)
            failures.append((key, str(e)))
    generate_site(dfs)
    # Write a small status json
    status = {
        "updated_at_beijing": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "failures": failures
    }
    open(os.path.join(SITE_DIR, "status.json"), "w").write(json.dumps(status, ensure_ascii=False, indent=2))
    print("Done.")

if __name__ == "__main__":
    main()
