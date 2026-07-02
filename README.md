# 台灣股票分析工具 (Taiwan Stock Analysis Tool)

AI 驅動的台灣股票分析系統，整合 TWSE 官方資料、技術分析、機器學習預測。

## 🚀 快速開始

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 啟動系統
python main.py

# 3. 自動開啟瀏覽器
#    → http://localhost:9999/app（儀表板）

# 4. 其他頁面
#    → http://localhost:9999/chat      AI 聊天
#    → http://localhost:9999/portfolio  虛擬倉位
#    → http://localhost:9999/report     研究報告
#    → http://localhost:9999/scheduler  排程管理
#    → http://localhost:9999/test       API 測試
#    → http://localhost:9999/docs       API 文件
```

## 功能特色

- 📊 **TWSE 官方資料整合** — 每日收盤行情、三大法人買賣超、融資融券
- 📈 **完整技術分析** — RSI、MACD、KD、布林通道、ATR、VWAP
- 🤖 **真實 ML 模型** — ARIMA、XGBoost、LSTM、集成模型
- 🗄️ **資料庫快取** — SQLite + SQLAlchemy ORM，自動快取資料
- 🌐 **Web 前端** — 即時股票分析儀表板
- 💼 **虛擬倉位** — 模擬投資、停損停利、投資回顧
- 📊 **研究報告** — 自動產生持股研究報告
- ⏰ **自動排程** — 內建排程服務，自動產生報告
- 🤖 **AI 聊天** — 問答式股票分析師

### 啟動伺服器

```bash
python main.py
```

### 訪問介面

- **前端頁面**: http://localhost:9999/app
- **API 文件**: http://localhost:9999/docs
- **健康檢查**: http://localhost:9999/health

## API 端點

### AI 分析

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/analysis/ai/{stock_id}` | GET | AI 綜合分析 |
| `/api/v1/analysis/report/{stock_id}` | GET | 文字分析報告 |

### TWSE 官方資料

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/twse/daily` | GET | 每日收盤行情 |
| `/api/v1/twse/institutional` | GET | 三大法人買賣超 |
| `/api/v1/twse/margin` | GET | 融資融券統計 |
| `/api/v1/twse/stock/{id}/history` | GET | 個股歷史資料 |

### 資料庫操作

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/db/sync/{stock_id}` | POST | 同步股票資料到資料庫 |
| `/api/v1/db/stocks` | GET | 資料庫中的股票列表 |

### 技術分析與預測

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/analysis/{stock_id}/technical` | GET | 技術分析 |
| `/api/v1/prediction/{stock_id}` | GET | ML 預測 |

## 專案結構

```
workspace/project/
├── agents/                  # AI Agent 整合
│   ├── openclaw_agent.py
│   └── hermes_agent.py
├── analysis/                # 分析模組
│   ├── stock_analyst.py     # AI 綜合分析引擎
│   ├── technical_analysis.py
│   ├── ml_prediction.py
│   ├── fundamental_analysis.py
│   └── valuation_analysis.py
├── api/                     # API 路由
│   ├── routes.py
│   └── services.py
├── config/                  # 配置
│   └── config.py
├── data/                    # 資料取得
│   ├── data_fetcher.py      # 整合多資料源
│   ├── stock_data.py        # 技術指標計算
│   └── twse_fetcher.py      # TWSE API 整合
├── models/                  # 資料模型
│   ├── database.py          # SQLAlchemy ORM
│   ├── db_manager.py        # 資料庫操作
│   ├── portfolio.py
│   └── recommendation.py
├── static/                  # 前端頁面
│   └── index.html
├── tests/                   # 單元測試
│   ├── test_technical_analysis.py
│   ├── test_ml_prediction.py
│   └── test_stock_analyst.py
├── docs/                    # 文件
│   └── DATABASE_DECISION.md
├── main.py                  # 主程式
└── README.md
```

## 技術決策

詳細的技術決策文件請參考：

- [資料庫選擇決策](docs/DATABASE_DECISION.md) — SQLite vs PostgreSQL vs DuckDB 的比較與選擇理由

## 範例使用

### 使用 curl 取得 AI 分析

```bash
curl "http://localhost:9999/api/v1/analysis/ai/2330.TW"
```

### 同步股票資料到資料庫

```bash
curl -X POST "http://localhost:9999/api/v1/db/sync/2330.TW?months=12"
```

### 取得 TWSE 每日收盤行情

```bash
curl "http://localhost:9999/api/v1/twse/daily"
```

## 富邦證券 SDK 整合

系統支援整合富邦證券 SDK，提供即時報價、完整財報、籌碼面數據。

### 架構

```
主電腦 (本機)                另一台電腦 (有富邦SDK)
┌──────────────────┐         ┌──────────────────┐
│ OpenClaw Agent   │  HTTP   │ 富邦 SDK 服務    │
│ 股票分析系統     │ ──────→ │ (fubon_service)  │
│ main.py          │         │ Port: 8081       │
└──────────────────┘         └──────────────────┘
```

### 安裝步驟

1. 在有富邦 SDK 的電腦上執行：
```bash
pip install -r requirements_fubon.txt
export FUBON_API_KEY=your_key
export FUBON_API_SECRET=your_secret
python fubon_service.py
```

2. 在主電腦連接：
```python
from agents.openclaw_agent import get_openclaw_agent
agent = get_openclaw_agent(fubon_service_url="http://192.168.1.100:8081")
result = await agent.analyze_stock("2330.TW")
```

詳細說明請參考 [富邦 SDK 整合指南](docs/FUBON_SETUP.md)

## 開發筆記

### TWSE API 注意事項

- 所有 API **免費**，無需註冊或 API Key
- 交易日 14:00 ~ 16:00 更新資料
- 非交易日回傳 HTML，程式已處理此情況
- 建議請求間隔 0.5 秒，避免被封鎖

### 資料庫

- 目前使用 **SQLite**（個人開發）
- 未來升級只需改連接字串，ORM 代碼不用改
- 詳見 [資料庫選擇決策](docs/DATABASE_DECISION.md)

### 財報數據來源

| 來源 | 免費? | 資料內容 |
|------|-------|---------|
| 公開資訊觀測站 (MOPS) | ✅ | 三大報表 |
| TWSE OpenAPI | ✅ | 基本財務指標 |
| Yahoo Finance | ✅ | 財報、估值 |
| **富邦證券 SDK** | ✅ | 即時報價、完整財報、籌碼 |

## 授權

MIT License