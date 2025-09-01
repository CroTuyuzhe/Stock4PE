import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time
from random import uniform

# 完整的请求头信息，模拟真实浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# 创建会话对象，保持连接和cookies
session = requests.Session()
session.headers.update(headers)

NASDAQ_API_KEY = "6XC-roD1G-yYTA668Uxy"

def fetch_with_retry(url, max_retries=3, is_gurufocus=False):
    """带重试机制的请求函数"""
    for attempt in range(max_retries):
        try:
            # 添加随机延迟，避免被识别为机器人
            time.sleep(uniform(1, 3))
            
            if is_gurufocus:
                # 对于GuruFocus，使用更真实的浏览器头
                gurufocus_headers = headers.copy()
                gurufocus_headers['Referer'] = 'https://www.gurufocus.com/'
                response = session.get(url, headers=gurufocus_headers, timeout=10)
            else:
                response = session.get(url, timeout=10)
                
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise e
            # 等待更长时间后重试
            time.sleep(uniform(2, 5))

def fetch_multpl(symbol):
    """获取Multpl数据"""
    url = f"https://data.nasdaq.com/api/v3/datasets/MULTPL/{symbol}.json?api_key={NASDAQ_API_KEY}"
    try:
        r = fetch_with_retry(url)
        j = r.json()
        return j["dataset"]["data"][0][1]
    except Exception as e:
        raise Exception(f"获取 {symbol} 数据失败: {str(e)}")

def scrape_gurufocus_pe(url):
    """从GuruFocus抓取PE数据"""
    try:
        r = fetch_with_retry(url, is_gurufocus=True)
        
        # 尝试多种解析方式
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 方法1: 尝试查找包含PE值的元素
        pe_elements = soup.find_all(string=re.compile(r"PE Ratio.*\d+\.\d+"))
        for element in pe_elements:
            match = re.search(r"(\d+\.\d+)", element)
            if match:
                return float(match.group(1))
        
        # 方法2: 尝试查找包含数值的大号字体元素
        large_texts = soup.find_all(["h1", "h2", "h3", "div"], class_=re.compile(r"text-|value-|number-"))
        for element in large_texts:
            text = element.get_text()
            match = re.search(r"(\d+\.\d+)", text)
            if match:
                return float(match.group(1))
        
        # 方法3: 搜索JSON数据
        json_pattern = re.search(r'"value":\s*"([0-9]+\.?[0-9]*)",', r.text)
        if json_pattern:
            return float(json_pattern.group(1))
            
        # 如果所有方法都失败，抛出异常
        raise ValueError("无法从页面中找到PE值")
    except Exception as e:
        raise Exception(f"解析GuruFocus页面失败: {str(e)}")

def fetch_data():
    """获取所有指数数据"""
    data = {}
    
    # CSI 300
    try:
        pe_value = scrape_gurufocus_pe("https://www.gurufocus.com/economic_indicators/4569/pe-ratio-ttm-for-the-csi-300-index")
        data["CSI300"] = {"pe": pe_value}
    except Exception as e:
        data["CSI300"] = {"pe": None, "error": str(e)}
        print(f"CSI300错误: {e}")

    # Nasdaq Composite
    try:
        pe_value = fetch_multpl("PCOMP_PE_RATIO_MONTH")
        data["Nasdaq"] = {"pe": pe_value}
    except Exception as e:
        data["Nasdaq"] = {"pe": None, "error": str(e)}
        print(f"Nasdaq错误: {e}")

    # S&P 500
    try:
        pe_value = fetch_multpl("SP500_PE_RATIO_MONTH")
        data["SP500"] = {"pe": pe_value}
    except Exception as e:
        data["SP500"] = {"pe": None, "error": str(e)}
        print(f"SP500错误: {e}")

    # Hang Seng Index
    try:
        pe_value = scrape_gurufocus_pe("https://www.gurufocus.com/economic_indicators/5732/pe-ratio-ttm-for-the-hang-seng-index")
        data["HSI"] = {"pe": pe_value}
    except Exception as e:
        data["HSI"] = {"pe": None, "error": str(e)}
        print(f"HSI错误: {e}")

    data["last_updated"] = datetime.utcnow().isoformat()
    return data

if __name__ == "__main__":
    try:
        result = fetch_data()
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("数据更新完成:", result)
    except Exception as e:
        print(f"脚本执行失败: {e}")
        # 创建空的data.json文件，避免GitHub Actions失败
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump({"error": str(e), "last_updated": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)
