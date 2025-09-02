import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import sys

def get_cpi_ppi_data():
    """爬取国家统计局的CPI和PPI数据并返回JSON格式数据"""
    try:
        # 国家统计局CPI数据页面
        cpi_url = "https://data.stats.gov.cn/easyquery.htm?cn=A01&zb=A0101&sj=2024"
        # 国家统计局PPI数据页面
        ppi_url = "https://data.stats.gov.cn/easyquery.htm?cn=A01&zb=A0102&sj=2024"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://data.stats.gov.cn/"
        }
        
        # 获取CPI数据
        cpi_response = requests.get(cpi_url, headers=headers)
        cpi_response.encoding = "utf-8"
        
        # 获取PPI数据
        ppi_response = requests.get(ppi_url, headers=headers)
        ppi_response.encoding = "utf-8"
        
        # 解析CPI数据
        cpi_soup = BeautifulSoup(cpi_response.text, 'html.parser')
        cpi_table = cpi_soup.find('table', class_='public_table')
        
        # 解析PPI数据
        ppi_soup = BeautifulSoup(ppi_response.text, 'html.parser')
        ppi_table = ppi_soup.find('table', class_='public_table')
        
        # 提取CPI数据
        cpi_data = []
        if cpi_table:
            rows = cpi_table.find_all('tr')[1:]  # 跳过表头
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    month = cols[0].text.strip()
                    value = cols[1].text.strip()
                    cpi_data.append({
                        "month": month,
                        "value": value,
                        "unit": "%"
                    })
        
        # 提取PPI数据
        ppi_data = []
        if ppi_table:
            rows = ppi_table.find_all('tr')[1:]  # 跳过表头
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    month = cols[0].text.strip()
                    value = cols[1].text.strip()
                    ppi_data.append({
                        "month": month,
                        "value": value,
                        "unit": "%"
                    })
        
        # 整理数据
        result = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpi": cpi_data,
            "ppi": ppi_data
        }
        
        return result
        
    except Exception as e:
        print(f"获取数据出错: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    # 获取数据并输出为JSON
    economic_data = get_cpi_ppi_data()
    if economic_data:
        print(json.dumps(economic_data, ensure_ascii=False, indent=4))
    else:
        sys.exit(1)
