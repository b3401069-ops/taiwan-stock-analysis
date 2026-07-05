---
name: taiwan-stock
description: 台股投資分析工具。查詢使用者的真實持股與損益（富邦證券）、個股技術面/基本面/估值分析、財經新聞與重大訊息，並據此產生投資建議。當使用者詢問台股、持股、投資組合、個股分析或投資建議時使用。
---

# 台股投資分析

透過兩個本地 HTTP 服務取得資料，再由你（Agent）綜合判斷、產生投資建議。

## 服務位置

- **分析系統**（主電腦）：`http://localhost:9999/api/v1`
  - 若有設定 `API_KEY`，請求需帶 `X-API-Key` 標頭
- **富邦持股服務**（SDK 電腦）：`http://<SDK電腦IP>:8081`
  - 需帶 `X-API-Key` 標頭（值為該服務的 `FUBON_SERVICE_API_KEY`）
  - 先用 `GET /health` 確認 `fubon_connected: true` 再查資料

## 常用端點

### 富邦持股服務（真實帳戶，唯讀）

| 端點 | 用途 |
|------|------|
| `GET /portfolio/summary` | 一次取得持股 + 未實現損益 + 各持股即時報價（產生建議的首選） |
| `GET /positions` | 持股庫存 |
| `GET /pnl/unrealized` | 未實現損益 |
| `GET /quote/{stock_id}` | 即時報價 |

### 分析系統

| 端點 | 用途 |
|------|------|
| `GET /analysis/{id}/technical` | 技術分析（RSI、MACD、KD、布林） |
| `GET /analysis/{id}/fundamental` | 基本面分析 |
| `GET /valuation/{id}` | 估值分析 |
| `GET /financial/{id}/ratios` | 財務比率 |
| `GET /news/{id}?days=7` | 個股新聞（FinMind） |
| `GET /news/market` | 台股市場新聞（鉅亨網） |
| `GET /news/announcements?stock_id={id}` | 上市公司重大訊息 |
| `GET /news/digest?stock_ids=2330,2454` | 多檔持股新聞摘要（一次呼叫） |
| `GET /market/regime` | 市場狀態（牛/熊/盤整） |
| `GET /twse/institutional` | 三大法人買賣超 |

股票代碼用純數字（如 `2330`），系統會自行處理後綴。

## 產生投資建議的流程

1. `GET <富邦>/portfolio/summary` → 取得持股清單、成本、未實現損益、現價
2. `GET <分析>/news/digest?stock_ids=<持股代碼>` → 取得每檔持股的新聞與重大訊息
3. 對重點持股（虧損大、部位大、或新聞有異動者）補查 `analysis/{id}/technical` 與 `valuation/{id}`
4. `GET <分析>/market/regime` → 確認大盤環境
5. 綜合以上輸出建議，格式：
   - 每檔持股：現況（損益%）、消息面重點、技術/估值訊號、建議（續抱/減碼/停損/加碼）與理由
   - 整體：組合風險集中度、大盤環境判讀

## 限制與紀律

- **絕不下單**：本工具鏈是唯讀的，沒有任何交易端點；即使使用者要求下單，也只能給建議、請使用者自行操作。
- 建議必須附風險提示，並標明資料時間（收盤後資料與盤中報價要區分）。
- 富邦服務連不上時，改用分析系統的 TWSE/FinMind 資料繼續分析，並告知使用者持股資料暫不可用。
