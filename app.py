from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

# 你的 Nasdaq DataLink API key
NASDAQ_API_KEY = "D6LJq9S9oorAZ_YVgiQn"

# ==============================
# 数据获取函数
# ==============================
def get_index_pe():
    data = {}

    # ✅ 沪深300（占位符，需换成你可用的API）
    data["csi300"] = {"name": "沪深300", "pe": None}  # TODO: Replace with actual API

    # ✅ 纳斯达克综合指数
    try:
        url = f"https://data.nasdaq.com/api/v3/datasets/MULTPL/PCOMP_PE_RATIO_MONTH.json?api_key={NASDAQ_API_KEY}"
        res = requests.get(url)
        js = res.json()
        value = js["dataset"]["data"][0][1]
        data["nasdaq"] = {"name": "纳斯达克综合", "pe": value}
    except Exception as e:
        data["nasdaq"] = {"name": "纳斯达克综合", "pe": None, "error": str(e)}

    # ✅ 标普500
    try:
        url = f"https://data.nasdaq.com/api/v3/datasets/MULTPL/SP500_PE_RATIO_MONTH.json?api_key={NASDAQ_API_KEY}"
        res = requests.get(url)
        js = res.json()
        value = js["dataset"]["data"][0][1]
        data["sp500"] = {"name": "标普500", "pe": value}
    except Exception as e:
        data["sp500"] = {"name": "标普500", "pe": None, "error": str(e)}

    # ✅ 恒生指数（占位符，需换成你可用的API）
    data["hsi"] = {"name": "恒生指数", "pe": None}  # TODO: Replace with actual API

    return data

# ==============================
# 路由
# ==============================
@app.route("/data")
def data():
    return jsonify(get_index_pe())

if __name__ == "__main__":
    app.run(debug=True)
