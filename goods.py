import requests
import json
from datetime import datetime
import time
from bs4 import BeautifulSoup

def fetch_cpi_data():
    """
    获取CPI（居民消费价格指数）数据，包含数据验证
    """
    try:
        url = "https://data.stats.gov.cn/easyquery.htm?cn=A01&zb=A0101&sj=last24"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://data.stats.gov.cn/"
        }
        
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        
        if response.status_code != 200:
            print(f"警告: CPI数据请求失败，状态码: {response.status_code}")
            return create_error_data("CPI", f"请求失败，状态码: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='public_table')
        
        if not table:
            print("警告: 未找到CPI数据表格")
            return create_error_data("CPI", "未找到数据表格")
        
        # 解析表格数据
        rows = table.find_all('tr')[1:]  # 跳过表头
        if not rows:
            print("警告: CPI数据表格为空")
            return create_error_data("CPI", "数据表格为空")
        
        cpi_data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                period = cols[0].text.strip()
                value = cols[1].text.strip()
                
                # 验证数据
                if validate_economic_data(value, "CPI", period):
                    cpi_data.append({
                        "period": period,
                        "value": float(value) if value else None,
                        "unit": "%"
                    })
        
        if not cpi_data:
            print("警告: 未解析到有效CPI数据")
            return create_error_data("CPI", "未解析到有效数据")
        
        return {
            "data": cpi_data,
            "data_quality": "good"
        }
        
    except Exception as e:
        print(f"获取CPI数据失败: {e}")
        return create_error_data("CPI", str(e))

def fetch_ppi_data():
    """
    获取PPI（工业生产者出厂价格指数）数据，包含数据验证
    """
    try:
        url = "https://data.stats.gov.cn/easyquery.htm?cn=A01&zb=A0102&sj=last24"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://data.stats.gov.cn/"
        }
        
        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"
        
        if response.status_code != 200:
            print(f"警告: PPI数据请求失败，状态码: {response.status_code}")
            return create_error_data("PPI", f"请求失败，状态码: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='public_table')
        
        if not table:
            print("警告: 未找到PPI数据表格")
            return create_error_data("PPI", "未找到数据表格")
        
        # 解析表格数据
        rows = table.find_all('tr')[1:]  # 跳过表头
        if not rows:
            print("警告: PPI数据表格为空")
            return create_error_data("PPI", "数据表格为空")
        
        ppi_data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                period = cols[0].text.strip()
                value = cols[1].text.strip()
                
                # 验证数据
                if validate_economic_data(value, "PPI", period):
                    ppi_data.append({
                        "period": period,
                        "value": float(value) if value else None,
                        "unit": "%"
                    })
        
        if not ppi_data:
            print("警告: 未解析到有效PPI数据")
            return create_error_data("PPI", "未解析到有效数据")
        
        return {
            "data": ppi_data,
            "data_quality": "good"
        }
        
    except Exception as e:
        print(f"获取PPI数据失败: {e}")
        return create_error_data("PPI", str(e))

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
    cpi_data = fetch_cpi_data()
    results["CPI"] = cpi_data
    time.sleep(2)  # 避免请求过于频繁
    
    print("正在获取PPI数据...")
    ppi_data = fetch_ppi_data()
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
    
