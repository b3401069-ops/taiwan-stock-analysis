# 富邦證券 SDK 整合指南

## 架構說明

```
┌─────────────────────────────────────────────────────────────────┐
│                        整體架構                                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   主電腦 (本機)       │         │  另一台電腦 (有富邦SDK) │
│                      │         │                      │
│  OpenClaw Agent      │  HTTP   │  富邦 SDK 服務       │
│  股票分析系統        │ ──────→ │  (fubon_service.py)  │
│  主程式 (main.py)    │         │                      │
│                      │         │  Port: 6666          │
└──────────────────────┘         └──────────────────────┘
         │
         │
         ▼
┌──────────────────────┐
│     GitHub API       │
│     TWSE API         │
│     Yahoo Finance    │
└──────────────────────┘
```

## 步驟 1：在另一台電腦安裝富邦 SDK

### 1.1 安裝 Python 依賴

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安裝服務依賴
pip install -r requirements_fubon.txt

# 再安裝富邦官方提供的 SDK wheel/installer（官方範例 import 名稱為 fubon_neo）
# 例：pip install path/to/fubon_neo-*.whl
```

### 1.2 下載服務程式

將以下檔案複製到另一台電腦：
- `fubon_service.py` - 富邦服務主程式
- `requirements_fubon.txt` - 依賴清單

## 步驟 2：設定環境變數

### Linux/Mac

```bash
# 設定富邦 API 認證（官方 Python 範例為身分證字號、密碼、憑證路徑、憑證密碼）
export FUBON_ID="你的身分證字號或登入 ID"
export FUBON_PASSWORD="你的登入密碼"
export FUBON_CERT_PATH="./你的憑證.pfx"
export FUBON_CERT_PASSWORD="你的憑證密碼"

# 設定服務端口（可選，預設 6666）
export FUBON_SERVICE_PORT=6666

# 建議設定：主電腦呼叫此服務時需帶相同 token
export FUBON_SERVICE_TOKEN="自訂一組長隨機字串"
```

### Windows (CMD)

```cmd
set FUBON_ID=你的身分證字號或登入 ID
set FUBON_PASSWORD=你的登入密碼
set FUBON_CERT_PATH=.\你的憑證.pfx
set FUBON_CERT_PASSWORD=你的憑證密碼
set FUBON_SERVICE_PORT=6666
set FUBON_SERVICE_TOKEN=自訂一組長隨機字串
```

### Windows (PowerShell)

```powershell
$env:FUBON_ID="你的身分證字號或登入 ID"
$env:FUBON_PASSWORD="你的登入密碼"
$env:FUBON_CERT_PATH=".\你的憑證.pfx"
$env:FUBON_CERT_PASSWORD="你的憑證密碼"
$env:FUBON_SERVICE_PORT=6666
$env:FUBON_SERVICE_TOKEN="自訂一組長隨機字串"
```

## 步驟 3：啟動富邦服務

```bash
# 啟動服務
python fubon_service.py
```

服務啟動後會顯示：
```
╔══════════════════════════════════════════════════════════════╗
║              富邦證券 SDK 服務                               ║
╠══════════════════════════════════════════════════════════════╣
║  API Key: ghp_Uhwy...                                       ║
║  狀態: 已連接                                                ║
║  端口: 6666                                                  ║
╠══════════════════════════════════════════════════════════════╣
║  API 端點:                                                   ║
║    GET /quote/{stock_id}         即時報價                   ║
║    GET /historical/{stock_id}    歷史資料                   ║
║    GET /financial/{stock_id}     財報數據                   ║
║    GET /institutional/{stock_id} 三大法人                   ║
║    GET /margin/{stock_id}        融資融券                   ║
║    GET /comprehensive/{stock_id} 綜合資料                   ║
╚══════════════════════════════════════════════════════════════╝
```

## 步驟 4：測試服務

### 4.1 健康檢查

```bash
curl http://localhost:6666/health
```

預期回應：
```json
{
  "status": "healthy",
  "fubon_connected": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

### 4.2 取得即時報價

```bash
curl http://localhost:6666/quote/2330
```

### 4.3 取得綜合資料

```bash
curl http://localhost:6666/comprehensive/2330
```

## 步驟 5：連接到主電腦的分析系統

### 5.1 修改主電腦配置

在主電腦的 `.env` 中加入：

```env
FUBON_SERVICE_URL=http://另一台電腦的IP:6666
FUBON_SERVICE_TOKEN=和另一台電腦相同的token
FUBON_REQUEST_TIMEOUT=10
```

### 5.2 使用 OpenClaw Agent

```python
from agents.openclaw_agent import get_openclaw_agent

# 指定富邦服務 URL
agent = get_openclaw_agent(fubon_service_url="http://192.168.1.100:6666")

# 分析股票（包含富邦數據）
result = await agent.analyze_stock("2330.TW", include_fubon=True)
print(result)
```

## API 端點說明

### 即時報價

```
GET /quote/{stock_id}

回傳格式:
{
  "success": true,
  "data": {
    "stock_id": "2330",
    "timestamp": "2024-01-01T12:00:00",
    "price_info": {
      "current": 1000.0,
      "open": 995.0,
      "high": 1010.0,
      "low": 990.0,
      "change": 5.0,
      "change_percent": 0.5
    },
    "volume_info": {
      "volume": 50000000,
      "amount": 50000000000
    },
    "orderbook": {
      "bid": [...],
      "ask": [...]
    }
  }
}
```

### 歷史資料

```
GET /historical/{stock_id}?days=365&interval=1d

參數:
- days: 歷史天數 (預設 365)
- interval: 資料間隔 (1m, 5m, 15m, 30m, 1h, 1d)

回傳格式:
{
  "success": true,
  "data": {
    "stock_id": "2330",
    "count": 365,
    "data": [
      {
        "date": "2024-01-01",
        "open": 995.0,
        "high": 1010.0,
        "low": 990.0,
        "close": 1000.0,
        "volume": 50000000
      },
      ...
    ]
  }
}
```

### 財報數據

```
GET /financial/{stock_id}?report_type=ratios

report_type 可選值:
- ratios: 財務比率
- income: 損益表
- balance: 資產負債表
- cashflow: 現金流量表

回傳格式:
{
  "success": true,
  "data": {
    "stock_id": "2330",
    "report_type": "ratios",
    "period": "2023Q4",
    "data": {
      "gross_margin": 55.2,
      "operating_margin": 45.8,
      "net_margin": 40.1,
      "eps": 32.5
    }
  }
}
```

### 三大法人

```
GET /institutional/{stock_id}

回傳格式:
{
  "success": true,
  "data": {
    "stock_id": "2330",
    "date": "2024-01-01",
    "foreign_buy": 1000000,
    "foreign_sell": 800000,
    "foreign_net": 200000,
    "trust_buy": 500000,
    "trust_sell": 300000,
    "trust_net": 200000,
    "dealer_buy": 100000,
    "dealer_sell": 80000,
    "dealer_net": 20000
  }
}
```

### 融資融券

```
GET /margin/{stock_id}

回傳格式:
{
  "success": true,
  "data": {
    "stock_id": "2330",
    "date": "2024-01-01",
    "margin_buy": 1000,
    "margin_sell": 800,
    "margin_balance": 50000,
    "short_buy": 500,
    "short_sell": 300,
    "short_balance": 10000
  }
}
```

## 故障排除

### 1. 無法連接富邦 SDK

```
錯誤: fubon_neo 未安裝
解決: 從富邦官方 SDK 下載頁下載 Python SDK wheel/installer 後安裝
```

### 2. 登入資訊或憑證錯誤

```
錯誤: 富邦 SDK 連接失敗
解決: 檢查 FUBON_ID、FUBON_PASSWORD、FUBON_CERT_PATH、FUBON_CERT_PASSWORD 是否正確
```

### 3. 無法連接服務

```
錯誤: requests.exceptions.ConnectionError
解決: 
1. 確認富邦服務已啟動
2. 確認防火牆允許 6666 端口
3. 確認 IP 地址正確
```

### 4. 端口被占用

```
錯誤: [Errno 98] Address already in use
解決: 
1. 更改端口: export FUBON_SERVICE_PORT=6667
2. 或殺死占用端口的程序: lsof -i :6666
```

## 安全注意事項

1. **不要將 API Key 提交到 Git**
   - 使用環境變數
   - 或使用 `.env` 檔案（已加入 .gitignore）

2. **限制服務訪問**
   - 只允許本地網路訪問
   - 或使用 VPN

3. **定期更換 API Key**
   - 每 3-6 個月更換一次

## 下一步

成功連接後，可以：

1. 使用即時報價進行自動交易
2. 使用財報數據進行基本面分析
3. 使用法人數據進行籌碼面分析
4. 結合 AI 進行綜合分析
