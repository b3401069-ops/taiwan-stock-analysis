# 富邦證券 SDK 整合指南（fubon_neo）

## 架構說明

```
┌──────────────────────┐         ┌──────────────────────────┐
│   主電腦 (本機)       │         │  另一台電腦 (有富邦SDK)   │
│                      │         │                          │
│  分析系統 main.py    │  HTTP   │  富邦 SDK 服務（唯讀）    │
│  (Port 9999)         │ ──────→ │  fubon_service.py        │
│  OpenClaw Agent      │         │  (Port 8081)             │
└──────────────────────┘         └──────────────────────────┘
```

富邦服務提供**唯讀**查詢：帳戶持股、未實現損益、交割銀行餘額、即時報價、歷史K線。
**不提供下單功能。**

## 事前準備（重要）

富邦新一代 API（Neo SDK）的登入方式是「**身分證字號 + 登入密碼 + 電子憑證**」，
不是 API Key/Secret。你需要：

1. 富邦證券帳戶，且已申請**新一代 API** 使用權（富邦 e 點通或官網申請）
2. 下載**電子憑證**（`.pfx` 檔）到執行服務的電腦，記下憑證密碼

## 步驟 1：安裝 SDK

```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac

pip install -r requirements_fubon.txt
```

若 `pip install fubon-neo` 失敗，到富邦官網「新一代API」下載對應平台的
wheel 檔，再 `pip install <檔名>.whl`。

## 步驟 2：設定環境變數

### Windows (PowerShell)

```powershell
$env:FUBON_PERSONAL_ID = "A123456789"          # 身分證字號
$env:FUBON_PASSWORD = "你的登入密碼"
$env:FUBON_CERT_PATH = "C:\certs\你的憑證.pfx"  # 憑證檔完整路徑
$env:FUBON_CERT_PASS = "憑證密碼"               # 沒有憑證密碼可不設
$env:FUBON_SERVICE_API_KEY = "自訂一組長隨機字串"  # 服務存取金鑰，強烈建議
$env:FUBON_SERVICE_PORT = "8081"               # 可選，預設 8081
```

### Linux/Mac

```bash
export FUBON_PERSONAL_ID="A123456789"
export FUBON_PASSWORD="你的登入密碼"
export FUBON_CERT_PATH="/home/user/certs/憑證.pfx"
export FUBON_CERT_PASS="憑證密碼"
export FUBON_SERVICE_API_KEY="自訂一組長隨機字串"
```

## 步驟 3：啟動服務

```bash
python fubon_service.py
```

啟動畫面會顯示 SDK 連線狀態與端點清單。若顯示「未連接」，檢查：
- 憑證路徑是否正確、憑證是否過期
- 身分證字號/密碼是否正確
- 是否已申請新一代 API 使用權

## 步驟 4：測試

```bash
# 健康檢查（免驗證）
curl http://localhost:8081/health

# 持股查詢（需帶金鑰）
curl -H "X-API-Key: 你的FUBON_SERVICE_API_KEY" http://localhost:8081/positions

# 投資組合全貌（持股 + 損益 + 報價）
curl -H "X-API-Key: 你的FUBON_SERVICE_API_KEY" http://localhost:8081/portfolio/summary
```

## API 端點

| 端點 | 說明 | 驗證 |
|------|------|------|
| `GET /health` | 健康檢查 | 免 |
| `GET /accounts` | 帳戶清單 | 要 |
| `GET /positions?account_index=0` | 持股庫存 | 要 |
| `GET /pnl/unrealized` | 未實現損益 | 要 |
| `GET /balance` | 交割銀行餘額 | 要 |
| `GET /portfolio/summary` | 持股+損益+即時報價 | 要 |
| `GET /quote/{stock_id}` | 即時報價 | 要 |
| `GET /historical/{stock_id}?days=365` | 歷史日K線 | 要 |

## 從主電腦連接

```bash
curl -H "X-API-Key: 金鑰" http://<SDK電腦IP>:8081/portfolio/summary
```

OpenClaw 整合請見 `openclaw_skills/taiwan-stock/SKILL.md`。

## 安全注意事項（必讀）

此服務回傳你的**真實持股與損益**，且綁定 `0.0.0.0`（整個區網可連）：

1. **一定要設定 `FUBON_SERVICE_API_KEY`**，並使用長隨機字串
2. **防火牆只放行主電腦的 IP** 連 8081 端口
   ```powershell
   # Windows 範例：只允許 192.168.1.50 連入 8081
   New-NetFirewallRule -DisplayName "Fubon Service" -Direction Inbound `
     -LocalPort 8081 -Protocol TCP -RemoteAddress 192.168.1.50 -Action Allow
   ```
3. **憑證檔與密碼不進 git**：`.pfx`、`.env` 都要在 `.gitignore`
4. 不要把此服務暴露到公網（不要設 port forwarding）

## 故障排除

| 症狀 | 處理 |
|------|------|
| `fubon_neo 未安裝` | `pip install fubon-neo` 或安裝官網 wheel |
| 登入失敗 | 檢查身分證字號/密碼/憑證路徑與密碼；確認已申請 API 使用權 |
| 行情未就緒（marketdata_ready: false） | 帳務查詢仍可用；檢查網路與行情權限 |
| 401 Unauthorized | 請求缺 `X-API-Key` 標頭或金鑰不符 |
| 主電腦連不上 | 確認服務已啟動、防火牆放行、IP 正確 |
