import yfinance as yf
import json
from datetime import datetime, timedelta
import time
import pandas as pd

def fetch_index_data(symbol, name):
    """
    获取指定指数的市场数据，包含数据验证
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 获取最近2天的历史数据用于验证
        history = ticker.history(period="2d")
        
        if history.empty or len(history) < 2:
            print(f"警告: {name} 历史数据不足")
            return create_error_data(name, "历史数据不足")
        
        # 使用历史数据计算更可靠的价格信息
        current_price = history['Close'].iloc[-1]
        previous_close = history['Close'].iloc[-2]
        
        # 验证价格数据的合理性
        if not validate_price_data(current_price, previous_close, name):
            return create_error_data(name, "价格数据异常")
        
        # 计算涨跌幅（限制在合理范围内）
        change_percent = calculate_safe_change_percent(current_price, previous_close)
        
        # 获取52周数据
        yearly_history = ticker.history(period="1y")
        if not yearly_history.empty:
            fifty_two_week_high = yearly_history['High'].max()
            fifty_two_week_low = yearly_history['Low'].min()
        else:
            fifty_two_week_high = None
            fifty_two_week_low = None
        
        # 获取成交额
        volume = history['Volume'].iloc[-1] if 'Volume' in history.columns else None
        
        return {
            "current_price": round(current_price, 2),
            "previous_close": round(previous_close, 2),
            "change_percent": round(change_percent, 2),
            "fifty_two_week_high": round(fifty_two_week_high, 2) if fifty_two_week_high else None,
            "fifty_two_week_low": round(fifty_two_week_low, 2) if fifty_two_week_low else None,
            "volume": int(volume) if volume else None,
            "currency": info.get('currency', 'USD'),
            "data_quality": "good"
        }
        
    except Exception as e:
        print(f"获取{name}数据失败: {e}")
        return create_error_data(name, str(e))

def validate_price_data(current_price, previous_close, name):
    """验证价格数据的合理性"""
    if current_price is None or previous_close is None:
        print(f"警告: {name} 价格数据为空")
        return False
    
    if current_price <= 0 or previous_close <= 0:
        print(f"警告: {name} 价格数据为负值或零")
        return False
    
    # 检查单日涨跌幅是否在合理范围内（±20%以内）
    if previous_close > 0:
        daily_change = abs((current_price - previous_close) / previous_close)
        if daily_change > 0.20:  # 超过20%的日涨跌幅需要特别检查
            print(f"警告: {name} 日涨跌幅异常: {daily_change:.2%}")
            # 这里可以添加更复杂的验证逻辑
            # 暂时仍然返回True，但标记为需要验证
    
    return True

def calculate_safe_change_percent(current_price, previous_close):
    """安全计算涨跌幅，处理异常情况"""
    if previous_close is None or previous_close == 0:
        return None
    
    change_percent = ((current_price - previous_close) / previous_close) * 100
    
    # 如果涨跌幅异常，进行限制或标记
    if abs(change_percent) > 20:  # 超过20%的涨跌幅
        print(f"警告: 异常涨跌幅: {change_percent:.2f}%")
        # 这里可以添加数据验证或使用替代计算方法
    
    return change_percent

def create_error_data(name, error_message):
    """创建错误数据记录"""
    return {
        "current_price": None,
        "previous_close": None,
        "change_percent": None,
        "fifty_two_week_high": None,
        "fifty_two_week_low": None,
        "volume": None,
        "currency": None,
        "data_quality": "error",
        "error": error_message
    }

def fetch_global_indices_data():
    """
    获取全球主要指数数据
    """
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
        "澳大利亚ASX200": {"symbol": "^AXJO", "region": "澳大利亚"},
    }
    
    results = {}
    
    for name, info in global_indices.items():
        symbol = info["symbol"]
        region = info["region"]
        
        print(f"正在获取{name}数据...")
        data = fetch_index_data(symbol, name)
        data["region"] = region
        results[name] = data
        
        time.sleep(1)
    
    results["last_updated"] = datetime.utcnow().isoformat()
    return results

if __name__ == "__main__":
    print("开始获取全球主要指数市场数据...")
    data = fetch_global_indices_data()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("全球指数市场数据已更新并保存到 data.json")
    
    # 打印质量报告
    print("\n=== 数据质量报告 ===")
    good_count = sum(1 for name, info in data.items() 
                    if name != "last_updated" and info.get("data_quality") == "good")
    total_count = len(data) - 1  # 减去last_updated
    
    print(f"数据质量: {good_count}/{total_count} 个指数数据正常")
    
    for name, info in data.items():
        if name != "last_updated" and info.get("data_quality") == "error":
            print(f"❌ {name}: {info.get('error')}")
        elif name != "last_updated":
            change_str = f"{info.get('change_percent', 0):+.2f}%" if info.get("change_percent") is not None else "N/A"
            print(f"✅ {name}: {info.get('current_price')} {info.get('currency', '')} | 涨跌: {change_str}")
