import yfinance as yf
import json
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup

def get_index_pe_ttm(symbol, name, is_etf=False):
    """获取指数的TTM市盈率"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 尝试获取TTM市盈率
        pe_ttm = info.get('trailingPE')
        
        # 如果直接获取失败，尝试计算TTM市盈率
        if pe_ttm is None:
            # 获取价格和每股收益
            price = info.get('regularMarketPrice') or info.get('currentPrice')
            eps_ttm = info.get('trailingEps')
            
            if price and eps_ttm and eps_ttm != 0:
                pe_ttm = price / eps_ttm
        
        # 获取当前价格和涨跌幅
        current_price = info.get('regularMarketPrice') or info.get('currentPrice')
        previous_close = info.get('previousClose')
        
        # 计算涨跌幅
        change_percent = None
        if current_price and previous_close and previous_close != 0:
            change_percent = ((current_price - previous_close) / previous_close) * 100
        
        result = {
            "pe_ttm": pe_ttm,
            "price": current_price,
            "change_percent": change_percent,
            "currency": info.get('currency', 'USD')
        }
        
        print(f"{name} PE TTM: {pe_ttm}")
        return result
        
    except Exception as e:
        print(f"获取{name}数据失败: {e}")
        return {
            "pe_ttm": None,
            "error": f"获取{name}数据失败: {str(e)}"
        }

def get_csi300_pe_ttm():
    """从国内数据源获取沪深300 PE TTM（备用方案）"""
    try:
        # 尝试从新浪财经获取
        url = "https://quote.eastmoney.com/zs000300.html"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找PE值
        pe_element = soup.find('span', id='pe_')
        if pe_element:
            return float(pe_element.text)
    except Exception as e:
        print(f"从备用源获取CSI300 PE失败: {e}")
    
    return None

def fetch_global_indices_data():
    """获取全球主要指数数据"""
    
    # 定义全球主要指数代码映射
    global_indices = {
        "沪深300": {"symbol": "000300.SS", "region": "中国"},
        "标普500": {"symbol": "^GSPC", "region": "美国"},
        "纳斯达克": {"symbol": "^IXIC", "region": "美国"},
        "道琼斯": {"symbol": "^DJI", "region": "美国"},
        "恒生指数": {"symbol": "^HSI", "region": "香港"},
        "日经225": {"symbol": "^N225", "region": "日本"},
        "台湾加权": {"symbol": "^TWII", "region": "台湾"},
        "韩国KOSPI": {"symbol": "^KS11", "region": "韩国"},
        "印度SENSEX": {"symbol": "^BSESN", "region": "印度"},
        "德国DAX": {"symbol": "^GDAXI", "region": "欧洲"},
        "英国富时100": {"symbol": "^FTSE", "region": "欧洲"},
        "法国CAC40": {"symbol": "^FCHI", "region": "欧洲"},
        "欧洲斯托克50": {"symbol": "^STOXX50E", "region": "欧洲"},
        "澳大利亚ASX200": {"symbol": "^AXJO", "region": "澳大利亚"},
        "巴西IBOVESPA": {"symbol": "^BVSP", "region": "拉丁美洲"},
        "俄罗斯MOEX": {"symbol": "IMOEX.ME", "region": "俄罗斯"},
        "越南胡志明": {"symbol": "VNINDEX.VN", "region": "东南亚"},
    }
    
    results = {}
    
    for name, info in global_indices.items():
        symbol = info["symbol"]
        region = info["region"]
        
        # 特殊处理沪深300（Yahoo Finance可能不提供PE数据）
        if name == "沪深300":
            data = get_index_pe_ttm(symbol, name)
            # 如果Yahoo Finance没有PE数据，尝试备用方案
            if data["pe_ttm"] is None:
                pe_ttm = get_csi300_pe_ttm()
                if pe_ttm:
                    data["pe_ttm"] = pe_ttm
        else:
            data = get_index_pe_ttm(symbol, name)
        
        data["region"] = region
        results[name] = data
        
        # 添加延迟，避免请求过于频繁
        time.sleep(1)
    
    # 添加更新时间
    results["last_updated"] = datetime.utcnow().isoformat()
    
    return results

if __name__ == "__main__":
    print("开始获取全球主要指数PE TTM数据...")
    data = fetch_global_indices_data()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("全球指数PE TTM数据已更新并保存到 data.json")
    
    # 打印摘要信息
    print("\n=== 全球主要指数PE TTM摘要 ===")
    for name, info in data.items():
        if name != "last_updated" and info.get("pe_ttm"):
            change_str = f"{info.get('change_percent', 0):+.2f}%" if info.get("change_percent") is not None else "N/A"
            print(f"{name}: {info['pe_ttm']:.2f} | 价格: {info.get('price', 'N/A')} {info.get('currency', '')} | 涨跌: {change_str}")
