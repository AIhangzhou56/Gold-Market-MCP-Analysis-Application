Below是一份示范 README.md，完全沿用 [a-share-mcp-is-just-i-need] 的章节与排版逻辑，但内容已替换为上海期货交易所黄金期货 (AU) 盘中行为 Model‑Content‑Protocol 服务器 / 量化分析工作台的实际实现。
你可以直接复制到项目根目录覆盖 README.md，再按需补充截图与二维码。

⸻



# shfe-gold-mcp <img src="resource/img/logo.png" width="90" align="right">

![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Package Manager](https://img.shields.io/badge/uv-supported-brightgreen)
![MCP](https://img.shields.io/badge/MCP-server-orange)

本项目是一个聚焦 **上海期货交易所黄金期货主力合约（AU）** 的 _Model Content Protocol_ (MCP) 服务器 + Streamlit 量化工作台。  
它集成沪金、COMEX GC、XAU/USD 三级市场数据，同步提取 **MCP 盘中行为信号**，并提供回测、报告与 API 服务，力求回答有关沪金日内交易模式的所有问题。

---

## 项目结构 <sup>（保持与 a-share-mcp 风格一致）</sup>

shfe_gold_mcp/
│
├── mcp_server.py              # MCP 服务器入口
├── pyproject.toml             # 依赖清单（uv / poetry 皆可）
├── README.md                  # 项目说明
│
├── src/                       # 源代码
│   ├── data/                  # 数据抓取与缓存
│   │   ├── fetch.py
│   │   ├── mapping.py
│   │   └── scheduler.py
│   ├── preprocess/            # 清洗与合约拼接
│   ├── features/              # MACD、VWAP、订单流等因子
│   ├── strategy/              # MCP 信号规则 & 回测
│   └── report/                # HTML → PDF 报告生成
│
├── app.py                     # Streamlit Web UI
└── resource/
└── img/                   # 页面 / README 插图
├── dashboard.png
└── mcp_signal_demo.png

（目录排版参考自 a‑share‑mcp 项目 README） [oai_citation:0‡GitHub](https://github.com/24mlight/a_share_mcp_is_just_I_need)

---

## 功能特点

| 分类 | 说明 |
|------|------|
| **实时数据** | Tushare 1 min / Tick 数据，自动主力映射；yfinance GC & XAU/USD 同步抓取 |
| **MCP 因子** | MACD、VWAP、主动买卖比、盘口深度、持仓Δ 等 10 + 指标 |
| **信号图谱** | 多因子热图，支持点击查看触发逻辑 |
| **策略回测** | 向量化日内回测、参数扫描、盈亏/回撤曲线 |
| **报告导出** | 一键生成含图表的 HTML/PDF |
| **MCP Server** | 提供 `get_gold_k_data`、`get_oi_delta`、`get_mcp_signal` 等工具函数 |

---

## 先决条件

1. **Python 3.10+**  
2. **依赖管理**：推荐 `uv`，亦支持 `pip`, `poetry`  
3. **API Key**  
   * Tushare `TUSHARE_TOKEN`  
   * Alpha Vantage `ALPHAVANTAGE_KEY`（可选，抓取 XAU/USD）  
4. **操作系统**：开发 & 部署均在 macOS / Linux 测试通过

---

## 数据更新时间

> *沪金 Tick/分钟数据在交易日结束后 ≈ 17:15 由交易所推送，夜盘次日 02:45 完成；  
> 国际金价由 yfinance 实时流式更新*。

- **日线 / 分钟线** 交易日当日 17:30 前后完成  
- **夜盘补数** 次日 03:00 前后完成  
- **Tick‑level** 抓取脚本实时写入本地 `/data/raw/tick_YYYYMMDD.csv`  

---

## 安装环境

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/shfe-gold-mcp.git
cd shfe-gold-mcp

# 2. 建立虚拟环境 & 安装依赖
uv venv && uv pip install -r requirements.txt   # or just: uv sync

# 3. 配置密钥（两种方式）
export TUSHARE_TOKEN="xxxxxxxxxxxxxxxxxxxx"
export ALPHAVANTAGE_KEY="xxxxxxxxxxxx"
# ──或──
cp config/secrets.example.toml config/secrets.toml



⸻

使用方法

1️⃣ 启动 MCP 服务器

uv run python mcp_server.py

在支持 MCP 的 IDE（VSCode / Cursor / CherryStudio）中添加如下 JSON：

"mcpServers": {
  "shfe-gold-mcp": {
    "command": "uv",
    "args": ["--directory", "/abs/path/shfe-gold-mcp", "run", "python", "mcp_server.py"],
    "transport": "stdio"
  }
}

2️⃣ 启动 Streamlit 工作台

streamlit run app.py

浏览器访问 http://localhost:8501 进入专业仪表盘界面。

⸻

工具列表（MCP）

类别	工具	描述
行情数据	get_gold_k_data	AU 主力 1min / Tick K 线
行情数据	get_gc_k_data	COMEX GC 连续合约
行情数据	get_xauusd_k_data	XAU/USD 现货
指标计算	calc_macd	快/慢线 & 柱状图
指标计算	calc_vwap	成交量加权均价
行为信号	get_mcp_signal	返回 bool + 触发因子
行为信号	get_signal_map	返回热图矩阵
报告	generate_daily_report	生成 HTML / PDF



⸻

贡献指南
	•	Issue 提交：请附上可复现步骤 / 样例日期
	•	PR：需通过 pytest + ruff + mypy 校验
	•	代码风格：PEP‑8, Black 120 cols

⸻

☕ 请作者喝杯咖啡

如果本项目对你有帮助，欢迎微信/支付宝打赏 ❤️


⸻

许可证

本项目遵循 MIT License。

---

### 使用说明

1. **目录占位符**  
   - 将 `resource/img/logo.png`、`dashboard.png` 等替换为你的实际截图；  
   - 若暂时没有，可先留空，GitHub 会忽略坏链。

2. **工具表 & 示例命令**  
   - 根据 `src/tools/…` 实际函数名修改表格；  
   - 如果不打算暴露 `mcp_server.py`，可删除对应章节。

3. **中英文混排**  
   - README 保持简体中文，如需英文版本可添加 `README.en.md`。

复制粘贴后，一键提交即可。祝你的沪金 MCP 项目早日开源亮相！