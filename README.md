# shfe-gold-mcp

![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Package Manager](https://img.shields.io/badge/uv-supported-brightgreen)
![MCP](https://img.shields.io/badge/MCP-server-orange)

本项目是一个聚焦 **上海期货交易所黄金期货主力合约（AU）** 的 _Model Content Protocol_ (MCP) 服务器 + Streamlit 量化工作台。  
它集成沪金、COMEX GC、XAU/USD 三级市场数据，同步提取 **MCP 盘中行为信号**，并提供回测、报告与 API 服务，力求回答有关沪金日内交易模式的所有问题。

---

## 项目结构

```
shfe_gold_mcp/
│
├── app.py                     # Streamlit 应用入口
├── pyproject.toml             # 依赖清单
├── README.md                  # 项目说明
│
├── assets/                    # 静态资源
│   └── logo.svg               # 项目标志
│
├── .streamlit/                # Streamlit 配置
│   └── config.toml            # 主题配置
│
├── data_fetchers/             # 数据获取
│   ├── alpha_vantage.py       # XAU/USD 数据源
│   ├── tushare_fetcher.py     # AU 主力合约数据源
│   └── yfinance_fetcher.py    # COMEX GC 数据源
│
├── data_processing/           # 数据处理
│   ├── cleaner.py             # 数据清洗
│   └── continuous_stitcher.py # 合约拼接
│
├── indicators/                # 技术指标
│   ├── technical.py           # MACD、VWAP等指标
│   └── orderflow.py           # 订单流分析
│
├── visualization/             # 可视化
│   ├── charts.py              # 图表生成
│   └── signal_maps.py         # 信号热图
│
├── backtesting/               # 回测模块
│   ├── strategy.py            # 策略定义
│   └── evaluator.py           # 回测评估
│
├── reporting/                 # 报告生成
│   ├── html_generator.py      # HTML报告
│   └── pdf_exporter.py        # PDF导出
│
├── utils/                     # 工具函数
│   └── helpers.py             # 辅助函数
│
└── database/                  # 数据库
    ├── manager.py             # 数据库管理
    └── models.py              # 数据模型
```

---

## 功能特点

| 分类 | 说明 |
|------|------|
| **实时数据** | Tushare 1 min / Tick 数据，自动主力映射；yfinance GC & XAU/USD 同步抓取 |
| **MCP 因子** | MACD、VWAP、主动买卖比、盘口深度、持仓Δ 等 10 + 指标 |
| **信号图谱** | 多因子热图，支持点击查看触发逻辑 |
| **策略回测** | 向量化日内回测、参数扫描、盈亏/回撤曲线 |
| **报告导出** | 一键生成含图表的 HTML/PDF |
| **MCP Server** | 提供 `get_gold_k_data`、`get_oi_delta`、`get_mcp_signal` 等工具函数 |

---

## 先决条件

1. **Python 3.10+**  
2. **依赖管理**：推荐 `uv`，亦支持 `pip`, `poetry`  
3. **API Key**  
   * Tushare `TUSHARE_TOKEN`  
   * Alpha Vantage `ALPHAVANTAGE_KEY`（可选，抓取 XAU/USD）  
4. **PostgreSQL 数据库**：用于存储市场数据和分析结果

---

## 数据更新时间

> *沪金 Tick/分钟数据在交易日结束后 ≈ 17:15 由交易所推送，夜盘次日 02:45 完成；  
> 国际金价由 yfinance 实时流式更新*。

- **日线 / 分钟线** 交易日当日 17:30 前后完成  
- **夜盘补数** 次日 03:00 前后完成  
- **Tick‑level** 抓取脚本实时写入本地数据库  

---

## 安装环境

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/shfe-gold-mcp.git
cd shfe-gold-mcp

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置密钥（环境变量）
export TUSHARE_TOKEN="your_token_here"
export ALPHAVANTAGE_KEY="your_key_here"

# 4. 创建PostgreSQL数据库
# 配置数据库连接（在环境变量中设置DATABASE_URL）
```

---

## 使用方法

### 启动Streamlit应用

```bash
streamlit run app.py
```

浏览器将自动打开访问：`http://localhost:8501`

### 应用功能

1. **数据分析**：加载和显示AU、COMEX GC和XAU/USD数据
2. **技术指标**：计算和显示各种技术指标（VWAP、MACD、RSI等）
3. **信号图谱**：生成相关性和技术指标信号图
4. **策略回测**：测试均值回归、趋势跟踪、突破和套利策略
5. **报告导出**：生成HTML和PDF报告

---

## 工具列表

| 类别 | 工具 | 描述 |
|-----|-----|-----|
| 行情数据 | `fetch_au_data` | AU 主力 1min / Tick K 线 |
| 行情数据 | `fetch_comex_gc` | COMEX GC 连续合约 |
| 行情数据 | `fetch_xau_usd` | XAU/USD 现货 |
| 指标计算 | `add_macd` | 快/慢线 & 柱状图 |
| 指标计算 | `add_vwap` | 成交量加权均价 |
| 行为信号 | `create_strategy` | 创建策略信号 |
| 行为信号 | `create_technical_signal_map` | 返回热图矩阵 |
| 报告 | `generate_html_report` | 生成 HTML 报告 |

---

## 贡献指南

- Issue 提交：请附上可复现步骤 / 样例日期
- PR：需通过代码质量检查
- 代码风格：PEP‑8

---

## 许可证

本项目遵循 MIT License。