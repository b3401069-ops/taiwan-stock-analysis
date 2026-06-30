# 台灣股票分析工具 - 快速入門指南

## 5分鐘快速開始

### 步驟1：安裝環境

```bash
# 複製專案
git clone <repository-url>
cd taiwan-stock-analysis-tool

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 步驟2：配置環境

```bash
# 複製配置文件
cp .env.example .env

# 編輯配置文件（至少需要配置以下項目）
nano .env
```

**最低配置要求：**
```env
# 必填：資料庫配置
DATABASE_URL=postgresql://username:password@localhost:5432/stock_analysis

# 選填：AI Agent配置（如需使用AI功能）
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# 選填：券商API配置（如需使用券商功能）
SHIOAJI_API_KEY=your_shioaji_api_key
SHIOAJI_SECRET_KEY=your_shioaji_secret_key
FUBON_API_KEY=your_fubon_api_key
FUBON_SECRET_KEY=your_fubon_secret_key
```

### 步驟3：啟動服務

```bash
# 啟動服務
python main.py
```

**成功啟動後，您將看到：**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 步驟4：訪問API文檔

打開瀏覽器，訪問：
- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc
- **健康檢查**：http://localhost:8000/health

---

## 快速功能體驗

### 1. 獲取台積電即時價格

```bash
curl -X GET "http://localhost:8000/api/v1/stocks/2330.TW/realtime"
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "stock_id": "2330.TW",
    "timestamp": "2024-01-15T10:30:00",
    "price": 600.0,
    "change": 10.0,
    "change_percent": 1.69,
    "volume": 12345678,
    "market_cap": 15000000000000,
    "pe_ratio": 20.5,
    "dividend_yield": 0.025
  }
}
```

### 2. 獲取技術分析

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/2330.TW/technical?indicators=rsi,macd,kd"
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "stock_id": "2330.TW",
    "indicators": {
      "rsi": {
        "latest": 65.5,
        "zone": "neutral"
      },
      "macd": {
        "latest": {
          "macd": 5.2,
          "signal": 4.8,
          "histogram": 0.4
        },
        "signal": "bullish"
      },
      "kd": {
        "latest": {
          "k": 72.3,
          "d": 68.5,
          "j": 79.9
        },
        "signal": "bullish",
        "zone": "neutral"
      }
    },
    "signals": {
      "overall_signal": "buy",
      "confidence": 0.7
    }
  }
}
```

### 3. 獲取買賣建議

```bash
curl -X GET "http://localhost:8000/api/v1/recommendation/2330.TW"
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "stock_id": "2330.TW",
    "overall_recommendation": {
      "recommendation": "buy",
      "confidence": "high",
      "weighted_score": 0.75,
      "reasoning": [
        "技術面顯示買入信號",
        "基本面表現良好",
        "估值偏低，具有投資價值",
        "機器學習預測上漲機率高"
      ]
    },
    "risk_assessment": {
      "risk_level": "medium",
      "risk_factors": ["波動性中等"],
      "risk_mitigation": ["設定停損點，控制單筆損失"]
    },
    "action_plan": {
      "immediate_action": "consider_buy",
      "entry_strategy": {
        "strategy": "conservative",
        "entry_price": "wait_for_dip",
        "position_size": "half_position"
      },
      "exit_strategy": {
        "take_profit": "10-15%",
        "stop_loss": "5-8%"
      }
    }
  }
}
```

### 4. 使用AI Agent對話

```bash
curl -X POST "http://localhost:8000/api/v1/agent/chat?message=請分析台積電的投資價值&agent_type=openclaw"
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "response": "台積電(2330.TW)是全球最大的半導體代工廠，在先進製程技術方面領先競爭對手...",
    "model": "gpt-4",
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 500,
      "total_tokens": 650
    }
  }
}
```

### 5. 獲取股價預測

```bash
curl -X GET "http://localhost:8000/api/v1/prediction/2330.TW?model=ensemble&days=30"
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "stock_id": "2330.TW",
    "model": "ensemble",
    "prediction_days": 30,
    "predictions": {
      "ensemble": {
        "predictions": [
          {
            "date": "2024-02-15",
            "predicted_price": 620.5,
            "confidence_interval": {
              "lower": 590.0,
              "upper": 650.0
            }
          }
        ],
        "trend": "up",
        "expected_return": 0.034,
        "model_agreement": 0.85
      }
    },
    "summary": {
      "trend": "up",
      "confidence": "high",
      "expected_return": 0.034,
      "recommendation": "buy"
    }
  }
}
```

---

## 常用API快速參考

### 股票資料
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/stocks` | GET | 獲取股票列表 |
| `/api/v1/stocks/{stock_id}` | GET | 獲取股票詳細資訊 |
| `/api/v1/stocks/{stock_id}/price` | GET | 獲取股票價格歷史 |
| `/api/v1/stocks/{stock_id}/realtime` | GET | 獲取即時股票價格 |

### 分析功能
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/analysis/{stock_id}/technical` | GET | 獲取技術分析 |
| `/api/v1/analysis/{stock_id}/fundamental` | GET | 獲取基本面分析 |
| `/api/v1/analysis/{stock_id}/valuation` | GET | 獲取估值分析 |
| `/api/v1/prediction/{stock_id}` | GET | 獲取股價預測 |

### 建議系統
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/recommendation/{stock_id}` | GET | 獲取買賣建議 |
| `/api/v1/recommendation/portfolio` | GET | 獲取投資組合建議 |

### AI Agent
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/agent/chat` | POST | AI Agent對話 |
| `/api/v1/agent/analysis/{stock_id}` | GET | AI Agent分析報告 |

### 券商API
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/broker/accounts` | GET | 獲取券商帳戶資訊 |
| `/api/v1/broker/order` | POST | 下單 |

### 系統狀態
| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/system/status` | GET | 獲取系統狀態 |
| `/health` | GET | 健康檢查 |

---

## 範例腳本

### Python範例

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def get_stock_price(stock_id):
    """獲取股票價格"""
    response = requests.get(f"{BASE_URL}/stocks/{stock_id}/realtime")
    return response.json()

def get_technical_analysis(stock_id):
    """獲取技術分析"""
    response = requests.get(f"{BASE_URL}/analysis/{stock_id}/technical")
    return response.json()

def get_recommendation(stock_id):
    """獲取買賣建議"""
    response = requests.get(f"{BASE_URL}/recommendation/{stock_id}")
    return response.json()

def chat_with_agent(message, agent_type="openclaw"):
    """與AI Agent對話"""
    response = requests.post(
        f"{BASE_URL}/agent/chat",
        params={"message": message, "agent_type": agent_type}
    )
    return response.json()

# 使用範例
if __name__ == "__main__":
    # 獲取台積電價格
    price = get_stock_price("2330.TW")
    print(f"台積電價格: {price['data']['price']}")
    
    # 獲取技術分析
    analysis = get_technical_analysis("2330.TW")
    print(f"技術分析信號: {analysis['data']['signals']['overall_signal']}")
    
    # 獲取買賣建議
    recommendation = get_recommendation("2330.TW")
    print(f"投資建議: {recommendation['data']['overall_recommendation']['recommendation']}")
    
    # 與AI Agent對話
    response = chat_with_agent("請分析台積電的投資價值")
    print(f"AI分析: {response['data']['response'][:200]}...")
```

### cURL範例

```bash
#!/bin/bash

# 獲取台積電即時價格
echo "=== 台積電即時價格 ==="
curl -s "http://localhost:8000/api/v1/stocks/2330.TW/realtime" | jq .

# 獲取技術分析
echo "=== 技術分析 ==="
curl -s "http://localhost:8000/api/v1/analysis/2330.TW/technical" | jq .

# 獲取買賣建議
echo "=== 買賣建議 ==="
curl -s "http://localhost:8000/api/v1/recommendation/2330.TW" | jq .

# 與AI Agent對話
echo "=== AI Agent對話 ==="
curl -s -X POST "http://localhost:8000/api/v1/agent/chat?message=請分析台積電的投資價值&agent_type=openclaw" | jq .
```

---

## 故障排除

### 1. 無法啟動服務

**問題**：`ModuleNotFoundError: No module named 'xxx'`
**解決**：
```bash
pip install -r requirements.txt
```

**問題**：`Connection refused` 資料庫連接失敗
**解決**：
```bash
# 檢查PostgreSQL服務
sudo systemctl status postgresql

# 建立資料庫
sudo -u postgres createdb stock_analysis
```

### 2. API回應錯誤

**問題**：`404 Not Found`
**解決**：檢查股票代碼格式（例如：2330.TW）

**問題**：`500 Internal Server Error`
**解決**：檢查日誌文件
```bash
tail -f logs/app.log
```

### 3. 效能問題

**問題**：API回應緩慢
**解決**：啟用Redis快取
```bash
# 啟動Redis
sudo systemctl start redis

# 配置Redis連接
echo "REDIS_URL=redis://localhost:6379/0" >> .env
```

---

## 下一步

1. **閱讀完整文檔**：[docs/usage_guide.md](docs/usage_guide.md)
2. **配置券商API**：[券商API整合指南](docs/usage_guide.md#券商api整合)
3. **配置AI Agent**：[AI Agent使用指南](docs/usage_guide.md#ai-agent使用指南)
4. **部署到生產環境**：[部署指南](docs/usage_guide.md#部署指南)

---

## 獲取幫助

- **API文檔**：http://localhost:8000/docs
- **GitHub Issues**：提交技術問題
- **社群討論**：GitHub Discussions

---

**免責聲明**：本工具僅供學習和研究使用，不構成投資建議。投資有風險，入市需謹慎。