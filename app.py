import yfinance as yf
import json
from datetime import datetime
import time

def fetch_index_data(symbol, name):
    """
    获取指定指数的市场数据
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        history = ticker.history(period="1y")
        
        # 获取当前价格
        current_price = info.get('regularMarketPrice') or info.get('currentPrice')
        
        # 获取52周最高最低（从一年历史数据中计算）
        if not history.empty:
            fifty_two_week_high = history['High'].max()
            fifty_two_week_low = history['Low'].min()
        else:
            fifty_two_week_high = None
            fifty_two_week_low = None
        
        # 获取前一日收盘价用于计算涨跌幅
        previous_close = info.get('previousClose')
        change_percent = None
        if current_price and previous_close and previous_close != 0:
            change_percent = ((current_price - previous_close) / previous_close) * 100
        
        # 尝试获取成交额数据
        volume = info.get('regularMarketVolume') or info.get('volume')
        
        return {
            "current_price": current_price,
            "fifty_two_week_high": fifty_two_week_high,
            "fifty_two_week_low": fifty_two_week_low,
            "change_percent": change_percent,
            "volume": volume,
            "currency": info.get('currency', 'USD')
        }
        
    except Exception as e:
        print(f"获取{name}数据失败: {e}")
        return {
            "current_price": None,
            "fifty_two_week_high": None,
            "fifty_two_week_low": None,
            "change_percent": None,
            "volume": None,
            "error": f"获取{name}数据失败: {str(e)}"
        }

def fetch_global_indices_data():
    """
    获取全球主要指数数据
    """
    # 定义全球主要指数代码映射
    global_indices = {
        "沪深300": {"symbol": "000300.SS", "region": "中国"},
        "上证指数": {"symbol": "000001.SS", "region": "中国"},
        "深证成指": {"symbol": "399001.SZ", "region": "中国"},
        "恒生指数": {"symbol": "^HSI", "region": "香港"},
        "标普500": {"symbol": "^GSPC", "region": "美国"},
        "纳斯达克": {"symbol": "^IXIC", "region": "美国"},
        "道琼斯": {"symbol": "^DJI", "region": "美国"},
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
    }
    
    results = {}
    
    for name, info in global_indices.items():
        symbol = info["symbol"]
        region = info["region"]
        
        print(f"正在获取{name}数据...")
        data = fetch_index_data(symbol, name)
        data["region"] = region
        results[name] = data
        
        # 添加延迟，避免请求过于频繁
        time.sleep(1)
    
    # 添加更新时间
    results["last_updated"] = datetime.utcnow().isoformat()
    
    return results

if __name__ == "__main__":
    print("开始获取全球主要指数市场数据...")
    data = fetch_global_indices_data()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("全球指数市场数据已更新并保存到 data.json")
    
    # 打印摘要信息
    print("\n=== 全球主要指数市场数据摘要 ===")
    for name, info in data.items():
        if name != "last_updated" and info.get("current_price"):
            change_str = f"{info.get('change_percent', 0):+.2f}%" if info.get("change_percent") is not None else "N/A"
            print(f"{name}: {info['current_price']} {info.get('currency', '')} | 涨跌: {change_str} | 52周高低: {info.get('fifty_two_week_high', 'N/A')}/{info.get('fifty_two_week_low', 'N/A')}")
