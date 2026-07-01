# 📱 Discord/Line 通知服務 - 使用說明

## 📋 目錄
1. [Discord 通知設定](#discord-通知設定)
2. [Line 通知設定](#line-通知設定)
3. [通知類型說明](#通知類型說明)
4. [實際使用範例](#實際使用範例)
5. [自動化排程](#自動化排程)
6. [常見問題](#常見問題)

---

## 🔵 Discord 通知設定

### 步驟 1: 建立 Discord Webhook

1. 開啟 Discord，進入你的伺服器
2. 點擊頻道名稱旁的齒輪圖示 → **編輯頻道**
3. 左側選單選擇 **整合** → **Webhook**
4. 點擊 **新增 Webhook**
5. 設定 Webhook 名稱（例如：股票分析機器人）
6. 選擇要發送的頻道
7. 點擊 **複製 Webhook URL**

### 步驟 2: 設定環境變數

**Linux/Mac:**
```bash
# 暫時設定（關閉終端後失效）
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/你的webhook-id/你的webhook-token"

# 永久設定（加入到 ~/.bashrc 或 ~/.zshrc）
echo 'export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/你的webhook-id/你的webhook-token"' >> ~/.bashrc
source ~/.bashrc
```

**Windows:**
```cmd
# 暫時設定
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/你的webhook-id/你的webhook-token

# 永久設定
setx DISCORD_WEBHOOK_URL "https://discord.com/api/webhooks/你的webhook-id/你的webhook-token"
```

### 步驟 3: 測試發送

```bash
# 使用 curl 測試
curl -X POST "http://localhost:9999/api/v1/notification/discord?content=測試訊息"

# 或使用 Python
python -c "
import requests
response = requests.post('http://localhost:9999/api/v1/notification/discord', params={'content': '測試訊息'})
print(response.json())
"
```

### 步驟 4: 確認收到訊息

檢查你的 Discord 頻道，應該會看到：
```
測試訊息
```

---

## 🟢 Line 通知設定

### 步驟 1: 取得 Line Notify Token

1. 前往 [Line Notify](https://notify-bot.line.me/)
2. 點擊右上角 **登入**，使用你的 Line 帳號登入
3. 登入後，點擊 **個人頁面**
4. 點擊 **發行權杖**
5. 輸入權杖名稱（例如：股票分析通知）
6. 選擇要發送的聊天室（個人或群組）
7. 點擊 **發行**
8. 複製權杖（只會顯示一次，請妥善保存）

### 步驟 2: 設定環境變數

**Linux/Mac:**
```bash
# 暫時設定
export LINE_NOTIFY_TOKEN="你的 Line Notify token"

# 永久設定
echo 'export LINE_NOTIFY_TOKEN="你的 Line Notify token"' >> ~/.bashrc
source ~/.bashrc
```

**Windows:**
```cmd
# 暫時設定
set LINE_NOTIFY_TOKEN=你的 Line Notify token

# 永久設定
setx LINE_NOTIFY_TOKEN "你的 Line Notify token"
```

### 步驟 3: 測試發送

```bash
# 使用 curl 測試
curl -X POST "http://localhost:9999/api/v1/notification/line?message=測試訊息"

# 或使用 Python
python -c "
import requests
response = requests.post('http://localhost:9999/api/v1/notification/line', params={'message': '測試訊息'})
print(response.json())
"
```

### 步驟 4: 確認收到訊息

檢查你的 Line 聊天室，應該會看到：
```
測試訊息
```

---

## 📊 通知類型說明

### 1. 一般訊息通知

**用途**: 發送一般文字訊息

**Discord API:**
```bash
curl -X POST "http://localhost:9999/api/v1/notification/discord" \
  -H "Content-Type: application/json" \
  -d '{"content": "台積電今日漲幅超過5%"}'
```

**Line API:**
```bash
curl -X POST "http://localhost:9999/api/v1/notification/line" \
  -H "Content-Type: application/json" \
  -d '{"message": "台積電今日漲幅超過5%"}'
```

### 2. 股票警報通知

**用途**: 發送股票價格警報（停損、停利、漲跌幅）

**參數說明:**
| 參數 | 說明 | 範例 |
|------|------|------|
| stock_id | 股票代碼 | 2330.TW |
| stock_name | 股票名稱 | 台積電 |
| alert_type | 警報類型 | 停損警報、停利警報、漲幅警報、跌幅警報 |
| message | 警報訊息 | 跌破支撐、突破壓力 |
| price | 目前價格 | 2400 |
| change_percent | 漲跌幅 | -2.5 |

**Discord API:**
```bash
curl -X POST "http://localhost:9999/api/v1/notification/discord/stock-alert?stock_id=2330.TW&stock_name=台積電&alert_type=停損警報&message=跌破支撐&price=2400&change_percent=-2.5"
```

**Line API:**
```bash
curl -X POST "http://localhost:9999/api/v1/notification/line/stock-alert?stock_id=2330.TW&stock_name=台積電&alert_type=停損警報&message=跌破支撐&price=2400&change_percent=-2.5"
```

**通知範例:**
```
🚨 停損警報: 台積電 (2330.TW)

📝 跌破支撐

💰 目前價格: NT$ 2,400.00
🔴 漲跌幅: -2.50%

⏰ 時間: 2026-07-01 15:30:00
```

### 3. 報告通知

**用途**: 發送分析報告（週報、月報、AI 摘要）

**參數說明:**
| 參數 | 說明 | 範例 |
|------|------|------|
| report_type | 報告類型 | 週報、月報、AI 選股摘要 |

**Discord API:**
```bash
curl -X POST "http://localhost:9999/api/v1/notification/discord/report?report_type=週報"
```

**Line API:**
```bash
curl -X POST "http://localhost:9999/api/v1/notification/line/report?report_type=週報"
```

### 4. 取得通知歷史

**用途**: 查看已發送的通知記錄

**API:**
```bash
curl "http://localhost:9999/api/v1/notification/history?limit=50"
```

---

## 📝 實際使用範例

### 範例 1: 每日股票監控腳本

建立檔案 `monitor.sh`:

```bash
#!/bin/bash

# 設定環境變數
export DISCORD_WEBHOOK_URL="你的 Discord Webhook URL"
export LINE_NOTIFY_TOKEN="你的 Line Notify Token"

# 監控股票列表
STOCKS=("2330.TW:台積電" "2317.TW:鴻海" "2454.TW:聯發科")

for stock_info in "${STOCKS[@]}"; do
    IFS=':' read -r STOCK_ID STOCK_NAME <<< "$stock_info"
    
    # 取得股票價格
    RESPONSE=$(curl -s "http://localhost:9999/api/v1/price/$STOCK_ID?period=1d")
    
    # 解析價格和漲跌幅
    PRICE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['summary']['latest_price'])" 2>/dev/null)
    CHANGE=$(echo $RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin)['data']['data']; print((data[-1]['close'] - data[-2]['close']) / data[-2]['close'] * 100)" 2>/dev/null)
    
    if [ -z "$PRICE" ] || [ -z "$CHANGE" ]; then
        echo "無法取得 $STOCK_NAME 的價格資料"
        continue
    fi
    
    # 判斷是否需要警報
    # 跌幅超過 3%
    if (( $(echo "$CHANGE < -3" | bc -l) )); then
        echo "⚠️ $STOCK_NAME 跌幅超過 3%: $CHANGE%"
        curl -X POST "http://localhost:9999/api/v1/notification/discord/stock-alert?stock_id=$STOCK_ID&stock_name=$STOCK_NAME&alert_type=跌幅警報&message=跌幅超過3%&price=$PRICE&change_percent=$CHANGE"
        curl -X POST "http://localhost:9999/api/v1/notification/line/stock-alert?stock_id=$STOCK_ID&stock_name=$STOCK_NAME&alert_type=跌幅警報&message=跌幅超過3%&price=$PRICE&change_percent=$CHANGE"
    fi
    
    # 漲幅超過 5%
    if (( $(echo "$CHANGE > 5" | bc -l) )); then
        echo "🎉 $STOCK_NAME 漲幅超過 5%: $CHANGE%"
        curl -X POST "http://localhost:9999/api/v1/notification/discord/stock-alert?stock_id=$STOCK_ID&stock_name=$STOCK_NAME&alert_type=漲幅警報&message=漲幅超過5%&price=$PRICE&change_percent=$CHANGE"
        curl -X POST "http://localhost:9999/api/v1/notification/line/stock-alert?stock_id=$STOCK_ID&stock_name=$STOCK_NAME&alert_type=漲幅警報&message=漲幅超過5%&price=$PRICE&change_percent=$CHANGE"
    fi
done

echo "監控完成"
```

**執行方式:**
```bash
chmod +x monitor.sh
./monitor.sh
```

### 範例 2: 每週報告腳本

建立檔案 `weekly_report.sh`:

```bash
#!/bin/bash

# 設定環境變數
export DISCORD_WEBHOOK_URL="你的 Discord Webhook URL"
export LINE_NOTIFY_TOKEN="你的 Line Notify Token"

echo "正在產生每週報告..."

# 1. 產生 AI 選股摘要
echo "產生 AI 選股摘要..."
curl -X POST "http://localhost:9999/api/v1/ai/summary?top_n=10" > /tmp/ai_summary.json

# 2. 產業輪動分析
echo "分析產業輪動..."
curl -s "http://localhost:9999/api/v1/industry/ranking?period=1w" > /tmp/industry_ranking.json

# 3. 概念股輪動分析
echo "分析概念股輪動..."
curl -s "http://localhost:9999/api/v1/concept/ranking?period=1w" > /tmp/concept_ranking.json

# 4. 發送報告通知
echo "發送報告通知..."
curl -X POST "http://localhost:9999/api/v1/notification/discord/report?report_type=每週報告"
curl -X POST "http://localhost:9999/api/v1/notification/line/report?report_type=每週報告"

echo "每週報告完成！"
```

**執行方式:**
```bash
chmod +x weekly_report.sh
./weekly_report.sh
```

### 範例 3: Python 自動化腳本

建立檔案 `auto_monitor.py`:

```python
#!/usr/bin/env python3
"""
自動化股票監控腳本
"""
import requests
import time
from datetime import datetime

# API 基礎 URL
API_BASE = "http://localhost:9999/api/v1"

# 監控股票列表
STOCKS = [
    {"id": "2330.TW", "name": "台積電", "stop_loss": -3, "take_profit": 5},
    {"id": "2317.TW", "name": "鴻海", "stop_loss": -5, "take_profit": 8},
    {"id": "2454.TW", "name": "聯發科", "stop_loss": -4, "take_profit": 6},
]

def get_stock_price(stock_id):
    """取得股票價格"""
    try:
        response = requests.get(f"{API_BASE}/price/{stock_id}?period=1d", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["data"]["summary"]["latest_price"]
    except Exception as e:
        print(f"取得 {stock_id} 價格失敗: {e}")
    return None

def get_stock_change(stock_id):
    """取得股票漲跌幅"""
    try:
        response = requests.get(f"{API_BASE}/price/{stock_id}?period=1d", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                prices = data["data"]["data"]
                if len(prices) >= 2:
                    last_close = prices[-1]["close"]
                    prev_close = prices[-2]["close"]
                    return (last_close - prev_close) / prev_close * 100
    except Exception as e:
        print(f"取得 {stock_id} 漲跌幅失敗: {e}")
    return None

def send_alert(stock_id, stock_name, alert_type, message, price, change):
    """發送警報"""
    try:
        # 發送 Discord 警報
        requests.post(
            f"{API_BASE}/notification/discord/stock-alert",
            params={
                "stock_id": stock_id,
                "stock_name": stock_name,
                "alert_type": alert_type,
                "message": message,
                "price": price,
                "change_percent": change
            },
            timeout=10
        )
        
        # 發送 Line 警報
        requests.post(
            f"{API_BASE}/notification/line/stock-alert",
            params={
                "stock_id": stock_id,
                "stock_name": stock_name,
                "alert_type": alert_type,
                "message": message,
                "price": price,
                "change_percent": change
            },
            timeout=10
        )
        
        print(f"✅ 已發送警報: {stock_name} {alert_type}")
    except Exception as e:
        print(f"❌ 發送警報失敗: {e}")

def monitor_stocks():
    """監控股票"""
    print(f"開始監控 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    
    for stock in STOCKS:
        stock_id = stock["id"]
        stock_name = stock["name"]
        stop_loss = stock["stop_loss"]
        take_profit = stock["take_profit"]
        
        # 取得價格和漲跌幅
        price = get_stock_price(stock_id)
        change = get_stock_change(stock_id)
        
        if price is None or change is None:
            print(f"⚠️ 無法取得 {stock_name} 的資料")
            continue
        
        print(f"{stock_name}: NT$ {price:.2f} ({change:+.2f}%)")
        
        # 檢查停損
        if change <= stop_loss:
            send_alert(
                stock_id, stock_name,
                "停損警報",
                f"跌幅達到 {stop_loss}%",
                price, change
            )
        
        # 檢查停利
        if change >= take_profit:
            send_alert(
                stock_id, stock_name,
                "停利警報",
                f"漲幅達到 {take_profit}%",
                price, change
            )
    
    print("監控完成\n")

def main():
    """主程式"""
    print("=" * 50)
    print("股票自動監控系統")
    print("=" * 50)
    
    # 設定監控間隔（秒）
    interval = 300  # 5 分鐘
    
    try:
        while True:
            monitor_stocks()
            print(f"等待 {interval} 秒後再次監控...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n監控已停止")

if __name__ == "__main__":
    main()
```

**執行方式:**
```bash
python auto_monitor.py
```

---

## ⏰ 自動化排程

### 使用 cron 排程 (Linux/Mac)

```bash
# 編輯 crontab
crontab -e

# 新增以下排程：

# 每天早上 9:00 執行監控
0 9 * * 1-5 /path/to/monitor.sh

# 每天下午 5:30 執行監控（收盤後）
30 17 * * 1-5 /path/to/monitor.sh

# 每週五下午 6:00 產生週報
0 18 * * 5 /path/to/weekly_report.sh

# 每月第一個週一早上 9:00 產生月報
0 9 1-7 * 1 /path/to/monthly_report.sh
```

### 使用 Windows 工作排程器

1. 開啟 **工作排程器**
2. 點擊 **建立基本工作**
3. 設定工作名稱（例如：股票監控）
4. 選擇觸發條件（每天、每週等）
5. 選擇執行動作（啟動程式）
6. 輸入腳本路徑
7. 完成設定

---

## ❓ 常見問題

### Q1: Discord 通知發送失敗？

**可能原因:**
1. Webhook URL 格式錯誤
2. 環境變數未設定
3. Discord 伺服器權限不足

**解決方法:**
```bash
# 檢查環境變數
echo $DISCORD_WEBHOOK_URL

# 測試 Webhook URL
curl -X POST "你的 Webhook URL" -H "Content-Type: application/json" -d '{"content": "測試"}'
```

### Q2: Line 通知發送失敗？

**可能原因:**
1. Token 已過期或被撤銷
2. 環境變數未設定
3. Line Notify 服務異常

**解決方法:**
```bash
# 檢查環境變數
echo $LINE_NOTIFY_TOKEN

# 重新發行 Token
# 前往 https://notify-bot.line.me/ 重新發行
```

### Q3: 如何查看通知歷史？

```bash
# 使用 API 查看
curl "http://localhost:9999/api/v1/notification/history?limit=50"

# 或使用 Python
python -c "
import requests
response = requests.get('http://localhost:9999/api/v1/notification/history')
print(response.json())
"
```

### Q4: 如何自訂通知格式？

修改 `services/notification.py` 中的格式化函數：

```python
def custom_format(self, stock_id, stock_name, message):
    """自訂通知格式"""
    return f"""
📊 股票分析通知
    
股票: {stock_name} ({stock_id})
訊息: {message}
時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
請注意風險管理！
    """
```

### Q5: 如何同時發送多個通知？

```bash
# 同時發送 Discord 和 Line
curl -X POST "http://localhost:9999/api/v1/notification/discord?content=訊息" &
curl -X POST "http://localhost:9999/api/v1/notification/line?message=訊息" &
wait
```

---

## 📚 相關資源

- [Discord Webhook 文件](https://discord.com/developers/docs/resources/webhook)
- [Line Notify 文件](https://notify-bot.line.me/doc/)
- [台灣股票分析工具 GitHub](https://github.com/b3401069-ops/taiwan-stock-analysis)

---

**最後更新**: 2026-07-01
**維護者**: OpenHands Agent
