# 🖥️ CLI 工具 - 使用說明

## 📋 目錄
1. [CLI 工具介紹](#cli-工具介紹)
2. [安裝與設定](#安裝與設定)
3. [基本使用](#基本使用)
4. [股票相關命令](#股票相關命令)
5. [多因子選股命令](#多因子選股命令)
6. [產業分析命令](#產業分析命令)
7. [概念股分析命令](#概念股分析命令)
8. [AI 分析命令](#ai-分析命令)
9. [市場分析命令](#市場分析命令)
10. [回測命令](#回測命令)
11. [進階使用](#進階使用)
12. [常見問題](#常見問題)

---

## 🎯 CLI 工具介紹

**是的！CLI 工具完全不需要使用網頁就可以操作！**

CLI (Command Line Interface) 工具是一個命令列介面，讓您可以：
- ✅ **直接在終端機操作**，不需要開啟瀏覽器
- ✅ **自動化執行**，可以寫成腳本排程執行
- ✅ **批次處理**，一次處理多個股票
- ✅ **整合其他系統**，可以與其他工具結合

### CLI vs Web 介面比較

| 功能 | CLI 工具 | Web 介面 |
|------|----------|----------|
| **使用方式** | 終端機命令 | 瀏覽器網頁 |
| **適合場景** | 自動化、批次處理 | 手動操作、視覺化 |
| **學習門檻** | 需要了解命令 | 圖形化操作 |
| **執行效率** | 快速、輕量 | 需要載入網頁 |
| **可攜性** | 可寫成腳本 | 需要瀏覽器 |
| **適用對象** | 開發者、自動化 | 一般使用者 |

---

## 🛠️ 安裝與設定

### 系統需求

- Python 3.8+
- 主伺服器已啟動 (`python main.py`)

### 安裝步驟

**1. 確認主伺服器已啟動**
```bash
# 啟動主伺服器
python main.py

# 確認伺服器運行中
curl http://localhost:9999/
```

**2. 確認 CLI 工具可用**
```bash
# 查看幫助
python cli.py --help
```

### 環境變數設定（可選）

如果要使用通知功能，需要設定環境變數：

```bash
# Discord 通知
export DISCORD_WEBHOOK_URL="你的 Discord Webhook URL"

# Line 通知
export LINE_NOTIFY_TOKEN="你的 Line Notify Token"
```

---

## 🚀 基本使用

### 查看所有可用命令

```bash
python cli.py --help
```

**輸出範例:**
```
usage: cli.py [-h] {stock,screener,industry,concept,ai,market,backtest} ...

台灣股票分析工具 - CLI

positional arguments:
  {stock,screener,industry,concept,ai,market,backtest}
                        可用命令
    stock               股票相關命令
    screener            多因子選股命令
    industry            產業分析命令
    concept             概念股分析命令
    ai                  AI 分析命令
    market              市場分析命令
    backtest            回測命令

options:
  -h, --help            show this help message and exit
```

### 查看子命令幫助

```bash
# 查看股票命令幫助
python cli.py stock --help

# 查看多因子選股命令幫助
python cli.py screener --help

# 查看產業分析命令幫助
python cli.py industry --help

# 查看概念股分析命令幫助
python cli.py concept --help

# 查看 AI 分析命令幫助
python cli.py ai --help

# 查看市場分析命令幫助
python cli.py market --help

# 查看回測命令幫助
python cli.py backtest --help
```

---

## 📈 股票相關命令

### 取得股票資訊

```bash
python cli.py stock info 2330.TW
```

**輸出範例:**
```
📊 股票資訊: 2330.TW
==================================================
{
  "stock_id": "2330.TW",
  "name": "台積電",
  "market": "上市",
  "industry": "半導體"
}
```

### 取得股票價格

```bash
# 取得 6 個月價格（預設）
python cli.py stock price 2330.TW

# 取得 1 年價格
python cli.py stock price 2330.TW --period 1y

# 取得 3 個月價格
python cli.py stock price 2330.TW --period 3mo
```

**輸出範例:**
```
📈 股票價格: 2330.TW
==================================================
期間: 6mo
資料筆數: 125

摘要:
  開始日期: 2026-01-02
  結束日期: 2026-07-01
  最新價格: 2450.00
  最高價格: 2600.00
  最低價格: 2200.00
  平均價格: 2400.00
```

### 取得估值指標

```bash
python cli.py stock valuation 2330.TW
```

**輸出範例:**
```
💰 估值指標: 2330.TW
==================================================
目前價格: 2450.00
本益比 (PE): 18.50
股價淨值比 (PB): 5.20
股利殖利率: 2.50%
估值評級: 合理
```

### 批次取得多檔股票資訊

```bash
# 建立批次腳本
for stock in 2330.TW 2317.TW 2454.TW 2308.TW 2412.TW; do
    echo "=== $stock ==="
    python cli.py stock info $stock
    echo ""
done
```

---

## 🔍 多因子選股命令

### 執行選股篩選

```bash
# 預設篩選前 10 名
python cli.py screener run

# 篩選前 20 名
python cli.py screener run --top-n 20

# 篩選前 5 名
python cli.py screener run --top-n 5
```

**輸出範例:**
```
🔍 多因子選股篩選
==================================================

篩選結果 (前 10 名):
--------------------------------------------------
 1. 台積電 (2330.TW)
    綜合分數: 0.7234
    目前價格: 2450.00

 2. 聯發科 (2454.TW)
    綜合分數: 0.6891
    目前價格: 1200.00

 3. 鴻海 (2317.TW)
    綜合分數: 0.6543
    目前價格: 180.50
```

### 更新因子權重

```bash
# 更新所有因子權重
python cli.py screener weights --momentum 0.3 --value 0.3 --quality 0.2 --size 0.1 --liquidity 0.05 --institutional 0.05

# 只更新動量因子權重
python cli.py screener weights --momentum 0.4

# 重設為預設權重
python cli.py screener weights --momentum 0.2 --value 0.25 --quality 0.25 --size 0.1 --liquidity 0.1 --institutional 0.1
```

**輸出範例:**
```
⚖️ 更新因子權重
==================================================
因子權重:
  momentum: 30.00%
  value: 30.00%
  quality: 20.00%
  size: 10.00%
  liquidity: 5.00%
  institutional: 5.00%

✅ 因子權重更新成功
```

---

## 🏭 產業分析命令

### 產業強度排名

```bash
# 取得 6 個月產業排名（預設）
python cli.py industry ranking

# 取得 3 個月產業排名
python cli.py industry ranking --period 3mo

# 取得 1 年產業排名
python cli.py industry ranking --period 1y
```

**輸出範例:**
```
🏭 產業強度排名
==================================================
 1. 半導體
    強度分數: 0.8424
    信號: strong_buy
    20日動量: 11.22%

 2. AI 概念
    強度分數: 0.7035
    信號: strong_buy
    20日動量: 6.53%

 3. 金融
    強度分數: 0.5547
    信號: buy
    20日動量: 10.14%

 4. 傳產
    強度分數: 0.5301
    信號: buy
    20日動量: 11.91%

 5. 電動車
    強度分數: 0.1354
    信號: hold
    20日動量: 0.83%
```

### 產業輪動分析

```bash
python cli.py industry rotation --period 6mo
```

**輸出範例:**
```
🔄 產業輪動分析
==================================================
最強產業: 半導體
最弱產業: 傳產
輪動機會: 1 個

輪動機會:
  • 傳產 → 半導體
    信號強度: 0.85
    預期報酬: 8.50%
    風險等級: 中
```

---

## 💡 概念股分析命令

### 概念股熱度排名

```bash
# 取得 6 個月概念股排名（預設）
python cli.py concept ranking

# 取得 3 個月概念股排名
python cli.py concept ranking --period 3mo
```

**輸出範例:**
```
💡 概念股熱度排名
==================================================
 1. 被動元件
    熱度分數: 0.8682
    趨勢: hot
    20日動量: 31.34%

 2. ABF 載板
    熱度分數: 0.8285
    趨勢: hot
    20日動量: 16.53%

 3. CoWoS 封裝
    熱度分數: 0.8157
    趨勢: hot
    20日動量: 12.87%

 4. 低軌衛星
    熱度分數: 0.6809
    趨勢: rising
    20日動量: 3.23%

 5. 散熱模組
    熱度分數: 0.6292
    趨勢: rising
    20日動量: 0.62%
```

### 熱門概念股

```bash
# 取得熱度 50% 以上的概念股（預設）
python cli.py concept hot

# 取得熱度 60% 以上的概念股
python cli.py concept hot --min-heat 0.6

# 取得熱度 80% 以上的概念股
python cli.py concept hot --min-heat 0.8
```

**輸出範例:**
```
🔥 熱門概念股
==================================================
📌 被動元件 (熱度: 0.87)
   描述: 電容、電阻等被動元件
   趨勢: hot
   股票數: 3

📌 ABF 載板 (熱度: 0.83)
   描述: ABF 載板產業，用於先進晶片封裝
   趨勢: hot
   股票數: 3

📌 CoWoS 封裝 (熱度: 0.82)
   描述: 台積電 CoWoS 先進封裝技術，用於 AI 晶片
   趨勢: hot
   股票數: 4
```

---

## 🤖 AI 分析命令

### AI 選股摘要

```bash
# 預設篩選前 10 名
python cli.py ai summary

# 篩選前 20 名
python cli.py ai summary --top-n 20

# 篩選前 5 名
python cli.py ai summary --top-n 5
```

**輸出範例:**
```
🤖 AI 選股摘要
==================================================

📋 執行摘要:

📊 AI 選股摘要報告

【市場狀態】
目前市場處於 多頭 狀態，信心水平 75%。
市場處於多頭格局，可積極佈局

【選股結果】
共篩選出 10 檔股票，推薦首選為 台積電。

【投資建議】
建議採用 積極成長策略，建議部位大小為 70-90%。

【風險提示】
投資有風險，請謹慎評估，建議定期檢視投資組合。

💡 投資建議:
  • 市場建議: 市場處於多頭格局，可積極佈局
  • 建議部位: 70-90%
  • 整體策略: 積極成長策略

⭐ 選股推薦:
  1. 台積電 (2330.TW) - 分數: 0.7234
  2. 聯發科 (2454.TW) - 分數: 0.6891
  3. 鴻海 (2317.TW) - 分數: 0.6543

⚠️ 風險提示:
  • 📊 所有分析僅供參考，不構成投資建議
  • 💰 投資有風險，請謹慎評估
  • 📈 建議定期檢視投資組合
```

---

## 📊 市場分析命令

### 市場狀態分析

```bash
python cli.py market regime
```

**輸出範例:**
```
📊 市場狀態分析
==================================================
市場狀態: 多頭
信心水平: 75%
建議動作: 積極佈局
分析原因: 加權指數站上所有均線，成交量放大
```

---

## 📈 回測命令

### Walk-Forward 驗證

```bash
# 基本用法
python cli.py backtest walk-forward 2330.TW rsi_oversold

# 完整參數
python cli.py backtest walk-forward 2330.TW rsi_oversold \
  --train-window 252 \
  --test-window 63 \
  --step-size 21 \
  --total-years 5
```

**參數說明:**
| 參數 | 說明 | 預設值 |
|------|------|--------|
| stock_id | 股票代碼 | 必填 |
| strategy | 策略名稱 | 必填 |
| --train-window | 訓練窗口（交易日） | 252 |
| --test-window | 測試窗口（交易日） | 63 |
| --step-size | 步進大小（交易日） | 21 |
| --total-years | 總回測年數 | 5 |

**可用策略:**
- `rsi_oversold` - RSI 超賣策略
- `macd_crossover` - MACD 黃金交叉策略
- `ma_crossover` - 均線交叉策略
- `bollinger_bounce` - 布林通道反彈策略
- `combined` - 組合策略

**輸出範例:**
```
🔄 Walk-Forward 驗證
==================================================
股票代碼: 2330.TW
策略名稱: rsi_oversold
總期間數: 20

績效指標:
  • 平均報酬率: 12.34%
  • 平均最大回撤: -8.56%
  • 平均勝率: 65.00%
  • 平均夏普比率: 1.23

整體指標:
  • 複合報酬率: 45.67%
  • 報酬率穩定性: 0.85
  • 風險調整後報酬: 1.45
  • 正報酬期間: 16
  • 負報酬期間: 4
```

---

## 🔧 進階使用

### 批次處理腳本

建立檔案 `batch_analysis.sh`:

```bash
#!/bin/bash

echo "=========================================="
echo "批次股票分析"
echo "=========================================="

# 股票列表
STOCKS=("2330.TW" "2317.TW" "2454.TW" "2308.TW" "2412.TW" "2881.TW" "2882.TW")

# 分析每檔股票
for stock in "${STOCKS[@]}"; do
    echo ""
    echo "=== 分析 $stock ==="
    python cli.py stock info $stock
    python cli.py stock valuation $stock
    echo "---"
done

echo ""
echo "=========================================="
echo "產業分析"
echo "=========================================="
python cli.py industry ranking --period 3mo
python cli.py industry rotation --period 3mo

echo ""
echo "=========================================="
echo "概念股分析"
echo "=========================================="
python cli.py concept ranking --period 3mo
python cli.py concept hot --period 3mo --min-heat 0.6

echo ""
echo "=========================================="
echo "AI 選股摘要"
echo "=========================================="
python cli.py ai summary --top-n 10

echo ""
echo "分析完成！"
```

**執行方式:**
```bash
chmod +x batch_analysis.sh
./batch_analysis.sh
```

### 自動化監控腳本

建立檔案 `auto_monitor.py`:

```python
#!/usr/bin/env python3
"""
自動化股票監控腳本
"""
import subprocess
import time
from datetime import datetime

def run_command(cmd):
    """執行命令並返回輸出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"錯誤: {e}"

def monitor():
    """監控股票"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始監控...")
    
    # 市場狀態
    print("\n📊 市場狀態:")
    output = run_command("python cli.py market regime")
    print(output)
    
    # 產業排名
    print("\n🏭 產業排名:")
    output = run_command("python cli.py industry ranking --period 3mo")
    print(output)
    
    # 概念股排名
    print("\n💡 概念股排名:")
    output = run_command("python cli.py concept ranking --period 3mo")
    print(output)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 監控完成")

def main():
    """主程式"""
    print("=" * 50)
    print("股票自動監控系統 (CLI)")
    print("=" * 50)
    
    # 設定監控間隔（秒）
    interval = 300  # 5 分鐘
    
    try:
        while True:
            monitor()
            print(f"\n等待 {interval} 秒後再次監控...")
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

### 整合到其他系統

```python
import subprocess
import json

def get_stock_info(stock_id):
    """取得股票資訊"""
    result = subprocess.run(
        f"python cli.py stock info {stock_id}",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout

def get_ai_summary(top_n=10):
    """取得 AI 選股摘要"""
    result = subprocess.run(
        f"python cli.py ai summary --top-n {top_n}",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout

# 使用範例
info = get_stock_info("2330.TW")
print(info)

summary = get_ai_summary(10)
print(summary)
```

---

## ❓ 常見問題

### Q1: CLI 工具無法連接？

**可能原因:**
1. 主伺服器未啟動
2. 連接埠錯誤
3. 網路問題

**解決方法:**
```bash
# 1. 確認主伺服器已啟動
python main.py

# 2. 測試連接
curl http://localhost:9999/

# 3. 檢查 API 基礎 URL
python -c "from cli import API_BASE; print(API_BASE)"
```

### Q2: 如何查看所有可用命令？

```bash
# 查看主命令
python cli.py --help

# 查看子命令
python cli.py stock --help
python cli.py screener --help
python cli.py industry --help
python cli.py concept --help
python cli.py ai --help
python cli.py market --help
python cli.py backtest --help
```

### Q3: 如何批次處理多檔股票？

```bash
# 方法 1: 使用迴圈
for stock in 2330.TW 2317.TW 2454.TW; do
    python cli.py stock info $stock
done

# 方法 2: 建立批次腳本
# 參考上文的批次處理腳本
```

### Q4: 如何將結果輸出到檔案？

```bash
# 輸出到文字檔
python cli.py industry ranking > industry_ranking.txt

# 輸出到 JSON 檔
python cli.py ai summary --top-n 10 > ai_summary.json

# 附加到檔案
python cli.py stock info 2330.TW >> stock_info.log
```

### Q5: 如何在腳本中使用 CLI？

```python
import subprocess

# 執行命令
result = subprocess.run(
    "python cli.py stock info 2330.TW",
    shell=True,
    capture_output=True,
    text=True
)

# 取得輸出
output = result.stdout
print(output)

# 檢查是否成功
if result.returncode == 0:
    print("命令執行成功")
else:
    print("命令執行失敗")
```

### Q6: CLI 和 Web API 有什麼不同？

| 功能 | CLI | Web API |
|------|-----|---------|
| **使用方式** | 命令列 | HTTP 請求 |
| **適合場景** | 自動化、批次 | 應用程式整合 |
| **輸出格式** | 文字 | JSON |
| **學習門檻** | 低 | 中 |
| **靈活性** | 高 | 高 |

---

## 📚 相關資源

- [台灣股票分析工具 GitHub](https://github.com/b3401069-ops/taiwan-stock-analysis)
- [API 文件](http://localhost:9999/docs)
- [Web 介面](http://localhost:9999/app)

---

**最後更新**: 2026-07-01
**維護者**: OpenHands Agent
