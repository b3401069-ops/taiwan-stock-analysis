# 資料庫選擇決策文件

## 決策樹

```
┌─────────────────────────────────────────────────────────┐
│                    選擇決策樹                            │
└─────────────────────────────────────────────────────────┘

需要多人同時存取？ ──→ 否 ──→ SQLite ✅
        │
        是
        │
        ▼
需要極快聚合查詢？ ──→ 是 ──→ ClickHouse / DuckDB
        │
        否
        │
        ▼
需要時序資料優化？ ──→ 是 ──→ TimescaleDB
        │
        否
        │
        ▼
PostgreSQL ✅
```

## 選擇 SQLite 的原因

1. **零配置** — 不需要安裝資料庫伺服器
2. **單檔案** — `taiwan_stock.db` 可以輕鬆備份、複製
3. **足夠快** — 對於個人使用的股票分析，SQLite 效能綽綽有餘
4. **SQLAlchemy 支援** — 未來要換 PostgreSQL 只需改一行連接字串

## 各資料庫比較

| 資料庫 | 類型 | 適用場景 | 優點 | 缺點 |
|--------|------|---------|------|------|
| **SQLite** (目前使用) | 嵌入式 | 個人開發、小型應用 | 零配置、單檔案、輕量 | 不支援高並發 |
| **PostgreSQL** | 關聯式 | 生產環境、多用戶 | 功能強大、支援 JSON | 需要安裝伺服器 |
| **DuckDB** | 列式分析 | 資料分析、OLAP | 極快的查詢速度 | 不適合頻繁寫入 |
| **ClickHouse** | 列式 | 時序資料分析 | 超快聚合查詢 | 學習成本高 |
| **TimescaleDB** | 時序 | 股票時序資料 | 專為時序優化 | 需要 PostgreSQL |
| **InfluxDB** | 時序 | 即時監控 | 專為時序設計 | 不適合關聯查詢 |
| **Redis** | 記憶體 | 快取、即時報價 | 極快讀寫 | 不適合長期儲存 |

## 未來升級路徑

所有升級只需修改連接字串，**ORM 模型和 CRUD 操作都不用改**：

```python
# SQLite (目前使用)
engine = create_engine("sqlite:///taiwan_stock.db")

# PostgreSQL (生產環境)
engine = create_engine("postgresql://user:password@localhost:5432/stockdb")

# DuckDB (資料分析)
engine = create_engine("duckdb:///stocks.duckdb")
```

## TWSE API 資料取得說明

### API 端點

| API | URL | 費用 | 認證 | 限制 |
|-----|-----|------|------|------|
| 每日收盤行情 | `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL` | **免費** | 無需 | 有隱性頻率限制 |
| 三大法人買賣超 | `https://openapi.twse.com.tw/v1/fund/T86` | **免費** | 無需 | 較嚴格的反爬蟲 |
| 個股歷史資料 | `https://www.twse.com.tw/exchangeReport/STOCK_DAY` | **免費** | 無需 | 當天資料要隔天才有 |
| 融資融券統計 | `https://openapi.twse.com.tw/v1/marginTrading/TFMSA` | **免費** | 無需 | 與 T86 同步更新 |

### 資料更新時間 (台灣時間 GMT+8)

```
09:00        13:30        14:00        15:00        16:00
  │            │            │            │            │
  ▼            ▼            ▼            ▼            ▼
開盤        最後成交      收盤        盤後處理      T86公布
交易中        交易中      (暫時)       結算中       三大法人
```

| API | 更新時間 | 說明 |
|-----|---------|------|
| **STOCK_DAY_ALL** (每日收盤) | **14:00 ~ 15:00** | 收盤後更新，但資料可能有延遲 |
| **T86** (三大法人) | **15:00 ~ 16:00** | 盤後公布，通常 16:00 前可取得 |
| **STOCK_DAY** (個股歷史) | **隨時可查** | 歷史資料，但當天資料要隔天才有 |
| **TFMSA** (融資融券) | **15:00 ~ 16:00** | 與 T86 同步更新 |

### 休市處理

非交易日或非交易時段，API 可能回傳 HTML 而非 JSON。程式已實作優雅處理：

```python
def _get_json(self, url: str, params=None):
    resp = self.session.get(url, params=params, timeout=15)
    content_type = resp.headers.get("content-type", "")
    
    if "json" not in content_type:
        # 非交易日或非交易時段
        logger.warning(f"TWSE API 回傳非 JSON 格式（可能休市）: {url}")
        return []  # 返回空列表，不會報錯
```

### 頻率限制

為避免被 TWSE 封鎖，實作了請求節流：

```python
REQUEST_INTERVAL = 0.5  # 每次請求間隔 0.5 秒
```

## 資料庫架構

### 資料表

| 表名 | 說明 | 主要欄位 |
|------|------|---------|
| `stocks` | 股票基本資料 | stock_id, name, market, industry |
| `prices` | 價格歷史 | stock_id, date, open, high, low, close, volume |
| `institutional_investors` | 三大法人 | date, stock_id, foreign_buy/sell, trust_buy/sell |
| `margin_trading` | 融資融券 | date, stock_id, margin_buy/sell, short_buy/sell |
| `indicator_cache` | 技術指標快取 | stock_id, date, indicator_type, value |
| `prediction_cache` | 預測結果快取 | stock_id, date, model, prediction |

### 資料流

```
用戶查詢 2330.TW 歷史資料
        │
        ▼
┌─────────────────────────────────────┐
│  DataFetcher.get_stock_price()      │
│                                     │
│  1. 先查 DB → 有資料 → 直接返回    │
│     │                               │
│     └─→ 無資料                      │
│           │                         │
│           ▼                         │
│  2. 嘗試 TWSE API                   │
│     │                               │
│     └─→ 成功 → 寫入 DB → 返回      │
│           │                         │
│           └─→ 失敗                  │
│                 │                   │
│                 ▼                   │
│  3. 降級 Yahoo Finance              │
│     │                               │
│     └─→ 寫入 DB → 返回             │
└─────────────────────────────────────┘
```
