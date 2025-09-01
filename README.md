# 全球主要指数 · 10年PE（TTM）数据看板

目标：每天 **北京时间 15:00** 自动更新并发布静态网站，展示 **沪深300、标普500、恒生指数、纳斯达克综合** 的最近 10 年市盈率（TTM）走势。

## 目录结构
```
pe-dashboard/
├─ config.json
├─ requirements.txt
├─ update_data.py        # 拉取数据 + 生成 site
├─ data/                 # 输出的 CSV（每个指数一份）
├─ site/
│   └─ index.html        # ECharts 看板（静态页，可托管到 Pages/Netlify/Nginx）
└─ .github/workflows/update.yml  # GitHub Actions 定时构建 & 发布
```

## 数据来源与链路（可核验）
- **标普500（S&P 500）TTM 市盈率**：Nasdaq Data Link（MULTPL 数据集），建议使用 `MULTPL/SP500_PE_RATIO_DAILY`，如不可用则回退 `..._MONTH`。  
  官方入口（需 API Key）：https://data.nasdaq.com/ （登录后搜索 `MULTPL SP500 PE` 获取 dataset code）
- **沪深300（CSI 300）TTM 市盈率**：中证指数有限公司（通过 AkShare 提供的 `stock_zh_index_value_csindex` 接口抓取）。  
  官网：https://www.csindex.com.cn/ ；AkShare 文档：https://akshare.akfamily.xyz/
- **恒生指数（HSI）TTM 市盈率**：优先尝试 **Hang Seng Indexes** 估值 JSON（你需要在 `HSI_JSON_URL` 中配置一条可访问的 JSON 源）；若无，则尝试 **GuruFocus 经济指标页面** 解析（可能需要登录 Cookie）。  
  HSIL 官网：https://www.hsi.com.hk/ ；GuruFocus 示例页：`PE Ratio (TTM) for the Hang Seng Index`。
- **纳斯达克综合（Nasdaq Composite）TTM 市盈率**：目前没有**长期稳定且免费**的可编程数据源。脚本提供两种方式：  
  1) 提供你自己的 CSV（`date,pe`）链接（环境变量 `NASDAQ_COMP_CSV`）；  
  2) 若你有付费/授权数据源（Bloomberg/Refinitiv/CEIC/Nasdaq Data Link Premium），可在 `update_data.py` 自定义 loader。

页面底部已生成醒目的来源标注：  
> 数据来源：Nasdaq Data Link（MULTPL）；中证指数（AkShare）；Hang Seng Indexes / GuruFocus；自定义数据源（纳斯达克综合）。 | 更新频率：每个交易日北京时间15:00自动更新

## 本地运行
```bash
cd pe-dashboard
export NASDAQ_API_KEY=你的NasdaqDataLinkKey
# 可选：export HSI_JSON_URL=https://.../hsi_pe.json
# 可选：export NASDAQ_COMP_CSV=https://.../nasdaq_composite_pe.csv

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python update_data.py

# 预览静态站点
./scripts/serve.sh  # 打开 http://localhost:8000
```

## 定时任务（Cron）
服务器在 **北京时区（UTC+8）**：
```cron
# 每个交易日（周一至周五）15:00 执行
0 15 * * 1-5 /ABS/PATH/pe-dashboard/scripts/cron_run.sh >> /ABS/PATH/pe-dashboard/cron.log 2>&1
```

## GitHub Pages 自动发布（推荐）
1. 新建一个公开仓库，将本项目提交。  
2. 在仓库 Settings → Secrets and variables → Actions 新增：
   - `NASDAQ_API_KEY`（必填）
   - `HSI_JSON_URL`（可选）
   - `NASDAQ_COMP_CSV`（建议你先用这个供数）
3. Settings → Pages：选择 **GitHub Actions** 作为发布源。  
4. workflow 每个交易日 **07:00 UTC（= 北京时间 15:00）** 触发，自动构建并把 `site/` 发布到 Pages。  
5. 你的访问链接形如：`https://<你的GitHub用户名>.github.io/<仓库名>/`。

## 前端说明
- 使用 **ECharts** 绘制多条折线，悬停显示某日各指数 PE；带标题、网格、轴标签；自适应 PC/移动端。
- 读取 `data/*.csv`（两列：`date,pe`），自动限制为最近 10 年区间。
- 脚注展示数据来源与更新频率。

## 风险与注意
- 不同机构对“TTM 市盈率”的口径（权重、负利润处理等）可能不同；跨市场对比仅供参考。
- HSI 与 Nasdaq Composite 的**免费可编程**数据源并不稳定。若你需要严格的每日自动化，请接入**授权**数据源，或将纳指替换为 **Nasdaq‑100 前瞻/TTM P/E**（有更多公开渠道）。
- 如需 Wind/Bloomberg/Refinitiv 接口范例，可在 `update_data.py` 增加自定义 loader。

---
若你希望我把你提供的专用 API 接入并替换临时方案，请把访问方式（或 CSV URL）给我即可。