import yfinance as yf
import json
from datetime import datetime
import time

def fetch_index_data():
    """获取主要指数数据"""
    
    # 定义指数代码映射
    index_symbols = {
        "CSI300": "000300.SS",  # 沪深300
        "SP500": "^GSPC",       # 标普500
        "Nasdaq": "^IXIC",      # 纳斯达克综合指数
        "HSI": "^HSI"           # 恒生指数
    }
    
    results = {}
    
    for name, symbol in index_symbols.items():
        try:
            # 获取指数数据
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 尝试获取PE比率（不同指数可能有不同的字段名）
            pe = (info.get('trailingPE') or 
                  info.get('forwardPE') or 
                  info.get('priceToEarnings'))
            
            # 获取当前价格
            current_price = info.get('regularMarketPrice') or info.get('currentPrice')
            
            # 获取52周最高最低
            year_high = info.get('fiftyTwoWeekHigh')
            year_low = info.get('fiftyTwoWeekLow')
            
            results[name] = {
                "pe": pe,
                "price": current_price,
                "year_high": year_high,
                "year_low": year_low,
                "currency": info.get('currency', 'USD')
            }
            
            print(f"{name} PE: {pe}")
            
        except Exception as e:
            results[name] = {
                "pe": None,
                "error": f"获取{name}数据失败: {str(e)}"
            }
            print(f"获取{name}数据失败: {e}")
        
        # 添加延迟，避免请求过于频繁
        time.sleep(1)
    
    results["last_updated"] = datetime.utcnow().isoformat()
    return results

if __name__ == "__main__":
    data = fetch_index_data()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("数据已更新并保存到 data.json")
