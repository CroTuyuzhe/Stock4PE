import requests
import json
from datetime import datetime
import time

def fetch_economic_data(indicator_code):
    """
    通过API获取经济指标数据
    indicator_code: 指标代码，CPI为"A0101"，PPI为"A0102"
    """
    try:
        # 使用国家统计局API接口
        url = "https://data.stats.gov.cn/easyquery.htm"
        params = {
            "m": "QueryData",
            "dbcode": "hgyd",
            "rowcode": "zb",
            "colcode": "sj",
            "wds": '[{"wdcode":"zb","valuecode":"%s"}]' % indicator_code,
            "dfwds": '[{"wdcode":"sj","valuecode":"last24"}]',
            "k1": int(time.time() * 1000)  # 时间戳，防止缓存
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://data.stats.gov.cn/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.encoding = "utf-8"
        
        if response.status_code != 200:
            print(f"警告: 数据请求失败，状态码: {response.status_code}")
            return create_error_data(indicator_code, f"请求失败，状态码: {response.status_code}")
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"警告: 无法解析{indicator_code}数据为JSON")
            return create_error_data(indicator_code, "数据解析失败")
        
        # 检查返回数据是否有效
        if "returndata" not in data or "datanodes" not in data["returndata"]:
            print(f"警告: {indicator_code}返回数据格式异常")
            return create_error_data(indicator_code, "返回数据格式异常")
        
        # 解析数据
        result_data = []
        for node in data["returndata"]["datanodes"]:
            # 提取时间和数值
            time_str = node["wds"][1]["valuecode"]
            value = node["data"]["data"]
            
            # 格式化时间
            if len(time_str) == 6:  # 形如202312表示2023年12月
                period = f"{time_str[:4]}年{time_str[4:]}月"
            else:
                period = time_str
            
            # 验证数据
            if validate_economic_data(value, indicator_code, period):
                result_data.append({
                    "period": period,
                    "value": float(value) if value and value != "-" else None,
                    "unit": "%"
                })
        
        # 按时间排序（最新的在前）
        result_data.sort(key=lambda x: x["period"], reverse=True)
        
        if not result_data:
            print(f"警告: 未解析到有效{indicator_code}数据")
            return create_error_data(indicator_code, "未解析到有效数据")
        
        return {
            "data": result_data,
            "data_quality": "good"
        }
        
    except Exception as e:
        print(f"获取{indicator_code}数据失败: {e}")
        return create_error_data(indicator_code, str(e))

def validate_economic_data(value, indicator, period):
    """验证经济数据的合理性"""
    if not value or value == "-":
        print(f"警告: {indicator} {period} 数据为空")
        return False
    
    try:
        value_float = float(value)
        # CPI和PPI通常不会出现极端波动，设置合理范围
        if not (-10 <= value_float <= 10):
            print(f"警告: {indicator} {period} 数据异常: {value}%")
            return False
        return True
    except ValueError:
        print(f"警告: {indicator} {period} 数据格式错误: {value}")
        return False

def create_error_data(indicator, error_message):
    """创建错误数据记录"""
    indicator_name = "CPI" if indicator == "A0101" else "PPI"
    return {
        "data": [],
        "data_quality": "error",
        "error": error_message
    }

def fetch_economic_indicators():
    """
    获取CPI和PPI经济指标数据
    """
    results = {}
    
    print("正在获取CPI数据...")
    cpi_data = fetch_economic_data("A0101")  # CPI指标代码
    results["CPI"] = cpi_data
    time.sleep(2)  # 避免请求过于频繁
    
    print("正在获取PPI数据...")
    ppi_data = fetch_economic_data("A0102")  # PPI指标代码
    results["PPI"] = ppi_data
    
    results["last_updated"] = datetime.utcnow().isoformat()
    return results

if __name__ == "__main__":
    print("开始获取CPI和PPI经济指标数据...")
    data = fetch_economic_indicators()
    
    with open("goods.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("CPI和PPI数据已更新并保存到 goods.json")
    
    # 打印质量报告
    print("\n=== 数据质量报告 ===")
    good_count = sum(1 for name, info in data.items() 
                    if name != "last_updated" and info.get("data_quality") == "good")
    total_count = len(data) - 1  # 减去last_updated
    
    print(f"数据质量: {good_count}/{total_count} 个指标数据正常")
    
    for name, info in data.items():
        if name != "last_updated":
            if info.get("data_quality") == "error":
                print(f"❌ {name}: {info.get('error')}")
            else:
                latest_data = info.get("data", [])[0] if info.get("data") else None
                if latest_data:
                    print(f"✅ {name}: 最新 {latest_data.get('period')} 为 {latest_data.get('value')}%")
                else:
                    print(f"ℹ️ {name}: 无可用数据")
    
