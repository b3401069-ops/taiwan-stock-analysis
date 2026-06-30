# 台灣股票分析工具 - 詳細使用指南

## 目錄

1. [快速開始](#快速開始)
2. [環境配置](#環境配置)
3. [功能詳細介紹](#功能詳細介紹)
4. [API使用範例](#api使用範例)
5. [AI Agent使用指南](#ai-agent使用指南)
6. [券商API整合](#券商api整合)
7. [常見問題解答](#常見問題解答)

---

## 快速開始

### 1. 安裝步驟

```bash
# 1. 複製專案
git clone <repository-url>
cd taiwan-stock-analysis-tool

# 2. 建立虛擬環境（建議）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 配置環境變數
cp .env.example .env
# 編輯 .env 文件，填入您的API密鑰

# 5. 啟動服務
python main.py
```

### 2. 驗證安裝

啟動服務後，訪問以下網址：
- **API文檔**：http://localhost:8000/docs
- **健康檢查**：http://localhost:8000/health
- **根目錄**：http://localhost:8000/

---

## 環境配置

### 1. 環境變數配置

編輯 `.env` 文件，配置以下參數：

```env
# 應用配置
APP_NAME=台灣股票分析工具
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# 資料庫配置
DATABASE_URL=postgresql://username:password@localhost:5432/stock_analysis
REDIS_URL=redis://localhost:6379/0

# 券商API配置
# 永豐金證券 Shioaji API
SHIOAJI_API_KEY=your_shioaji_api_key
SHIOAJI_SECRET_KEY=your_shioaji_secret_key

# 富邦證券API
FUBON_API_KEY=your_fubon_api_key
FUBON_SECRET_KEY=your_fubon_secret_key

# AI Agent配置
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# OpenClaw配置
OPENCLAW_API_URL=http://localhost:8000
OPENCLAW_API_KEY=your_openclaw_api_key

# Hermes配置
HERMES_API_URL=http://localhost:8001
HERMES_API_KEY=your_hermes_api_key
```

### 2. 資料庫設置

#### PostgreSQL設置
```bash
# 安裝PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 建立資料庫
sudo -u postgres psql
CREATE DATABASE stock_analysis;
CREATE USER stock_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE stock_analysis TO stock_user;
\q
```

#### Redis設置（可選）
```bash
# 安裝Redis
sudo apt-get install redis-server

# 啟動Redis
sudo systemctl start redis
sudo systemctl enable redis
```

---

## 功能詳細介紹

### 1. 資料取得功能

#### 支援的資料來源
- **Yahoo Finance**：全球股票市場數據（免費）
- **TWSE官方資料**：台灣證券交易所數據（免費）
- **永豐金證券Shioaji API**：即時報價、下單功能（免費，需開戶）
- **富邦證券API**：股票、期貨交易（免費，需開戶）

#### 支援的市場
- **台灣股市**：TWSE、OTC
- **日本股市**：Nikkei、TOPIX
- **韓國股市**：KOSPI、KOSDAQ
- **美國股市**：S&P500、NASDAQ、DOW

### 2. 技術分析功能

#### 移動平均線
- **SMA（簡單移動平均線）**：5、10、20、50、100、200日
- **EMA（指數移動平均線）**：5、10、20、50、100、200日
- **黃金交叉/死亡交叉**：50日與200日移動平均線交叉

#### 動量指標
- **RSI（相對強弱指標）**：14日RSI，超買(70)、超賣(30)
- **MACD**：12、26、9日參數，金叉/死叉信號
- **KD隨機指標**：9、3、3日參數，超買(80)、超賣(20)

#### 波動性指標
- **布林通道**：20日移動平均線 ± 2倍標準差
- **布林帶寬度**：衡量市場波動性
- **%B指標**：價格在布林通道中的位置

#### 成交量指標
- **成交量移動平均線**：20日成交量平均
- **成交量比率**：當前成交量與平均成交量的比率
- **OBV（能量潮指標）**：累積成交量指標

### 3. 基本面分析功能

#### 財務比率分析
- **獲利能力**：毛利率、營業利益率、淨利率
- **償債能力**：負債比率、流動比率、速動比率
- **營運效率**：資產週轉率、存貨週轉率
- **現金流**：營業現金流對淨利比率

#### 成長性分析
- **營收成長率**：年度營收變化
- **淨利成長率**：年度淨利變化
- **EPS成長率**：每股盈餘成長

#### 穩定性分析
- **營收波動性**：營收穩定性評估
- **淨利波動性**：淨利穩定性評估
- **現金流穩定性**：現金流穩定性評估

### 4. 估值分析功能

#### 相對估值法
- **本益比(PE)**：股價/每股盈餘，適用於獲利穩定的公司
- **股價淨值比(PB)**：股價/每股淨資產，適用於資產密集型產業
- **股利殖利率**：每股股利/股價，適用於穩定配息的公司
- **企業價值/EBITDA**：跨資本結構比較
- **自由現金流收益率**：每股自由現金流/股價

#### 絕對估值法
- **DCF現金流折現模型**：適用於有穩定現金流的公司
- **股利折現模型(DDM)**：適用於穩定配息的公司

#### 綜合估值策略
```
估值評分 = 
  PE評分 × 30% +
  PB評分 × 20% +
  股利殖利率評分 × 20% +
  EV/EBITDA評分 × 15% +
  自由現金流評分 × 15%
```

### 5. 機器學習預測功能

#### 支援的模型
- **ARIMA**：自回歸整合移動平均模型，適用於短期預測
- **LSTM**：長短期記憶網路，適用於時間序列預測
- **XGBoost**：梯度提升樹，適用於特徵豐富的預測
- **Transformer**：注意力機制模型，適用於複雜模式識別
- **集成學習**：結合多個模型的預測結果

#### 預測功能
- **股價預測**：1天、5天、10天、20天、30天預測
- **趨勢識別**：上漲、下跌、盤整趨勢
- **波動性預測**：預測未來波動性
- **異常偵測**：識別異常價格變動

### 6. AI Agent整合功能

#### OpenClaw Agent（OpenAI GPT-4）
- **自然語言查詢**：用自然語言詢問股票相關問題
- **智能分析報告**：自動生成股票分析報告
- **投資建議**：提供投資建議和風險評估

#### Hermes Agent（DeepSeek V4 Pro）
- **深度分析**：更深入的股票分析
- **預測模型**：更精確的預測模型
- **風險評估**：更全面的風險評估

#### MCP工具整合
- **Model Context Protocol**：標準化的工具整合協議
- **可擴展性**：支持自定義工具和插件
- **無縫整合**：與現有AI系統無縫整合

### 7. 國際股市連動分析

#### 連動分析功能
- **相關性分析**：計算不同市場之間的相關性
- **領先落後指標**：識別領先和落後的市場
- **風險傳導分析**：分析風險在不同市場間的傳導

#### 支援的市場
- **台灣加權指數(TAIEX)**：台灣主要市場指數
- **日經225指數(Nikkei)**：日本主要市場指數
- **韓國綜合指數(KOSPI)**：韓國主要市場指數
- **標普500指數(S&P500)**：美國主要市場指數
- **納斯達克指數(NASDAQ)**：美國科技股指數

### 8. 投資建議系統

#### 買賣建議生成
- **技術面建議**：基於技術指標的買賣信號
- **基本面建議**：基於財務分析的投資建議
- **估值建議**：基於估值模型的投資建議
- **綜合建議**：結合所有分析的綜合建議

#### 風險評估
- **波動率風險**：基於歷史波動率的風險評估
- **Beta風險**：基於市場敏感度的風險評估
- **流動性風險**：基於成交量的風險評估
- **集中度風險**：基於投資組合集中度的風險評估

#### 投資組合優化
- **風險等級**：低風險、中風險、高風險
- **資產配置**：股票、現金、債券配置
- **產業配置**：不同產業的配置比例
- **再平衡策略**：定期再平衡策略

---

## API使用範例

### 1. 獲取股票列表

```bash
# 獲取台灣股市股票列表
curl -X GET "http://localhost:8000/api/v1/stocks?market=taiwan"

# 獲取特定產業的股票
curl -X GET "http://localhost:8000/api/v1/stocks?market=taiwan&industry=半導體"
```

### 2. 獲取股票價格

```bash
# 獲取台積電(2330.TW)的價格歷史
curl -X GET "http://localhost:8000/api/v1/stocks/2330.TW/price?period=1y"

# 獲取即時價格
curl -X GET "http://localhost:8000/api/v1/stocks/2330.TW/realtime"
```

### 3. 技術分析

```bash
# 獲取台積電的技術分析
curl -X GET "http://localhost:8000/api/v1/analysis/2330.TW/technical"

# 指定技術指標
curl -X GET "http://localhost:8000/api/v1/analysis/2330.TW/technical?indicators=rsi,macd,kd"
```

### 4. 基本面分析

```bash
# 獲取台積電的基本面分析
curl -X GET "http://localhost:8000/api/v1/analysis/2330.TW/fundamental"
```

### 5. 估值分析

```bash
# 獲取台積電的估值分析
curl -X GET "http://localhost:8000/api/v1/analysis/2330.TW/valuation"

# 指定估值模型
curl -X GET "http://localhost:8000/api/v1/analysis/2330.TW/valuation?models=pe,pb,dividend_yield"
```

### 6. 股價預測

```bash
# 使用集成模型預測台積電股價30天
curl -X GET "http://localhost:8000/api/v1/prediction/2330.TW?model=ensemble&days=30"

# 使用特定模型預測
curl -X GET "http://localhost:8000/api/v1/prediction/2330.TW?model=lstm&days=10"
```

### 7. 買賣建議

```bash
# 獲取台積電的買賣建議
curl -X GET "http://localhost:8000/api/v1/recommendation/2330.TW"

# 獲取投資組合建議
curl -X GET "http://localhost:8000/api/v1/recommendation/portfolio?risk_level=medium&investment_amount=1000000"
```

### 8. AI Agent對話

```bash
# 與OpenClaw Agent對話
curl -X POST "http://localhost:8000/api/v1/agent/chat?message=請分析台積電的投資價值&agent_type=openclaw"

# 與Hermes Agent對話
curl -X POST "http://localhost:8000/api/v1/agent/chat?message=請預測台積電未來一個月的股價走勢&agent_type=hermes"
```

### 9. 券商API操作

```bash
# 獲取券商帳戶資訊
curl -X GET "http://localhost:8000/api/v1/broker/accounts?broker=shioaji"

# 下單購買台積電
curl -X POST "http://localhost:8000/api/v1/broker/order?stock_id=2330.TW&action=buy&quantity=1000&price=600.0&broker=shioaji"
```

### 10. 國際股市連動分析

```bash
# 獲取國際股市連動分析
curl -X GET "http://localhost:8000/api/v1/global/correlation?markets=taiwan,japan,korea,usa"
```

---

## AI Agent使用指南

### 1. OpenClaw Agent（OpenAI GPT-4）

#### 基本對話
```python
import requests

# 與OpenClaw Agent對話
response = requests.post(
    "http://localhost:8000/api/v1/agent/chat",
    params={
        "message": "請分析台積電(2330.TW)的投資價值",
        "agent_type": "openclaw"
    }
)

print(response.json())
```

#### 分析報告
```python
# 獲取AI分析報告
response = requests.get(
    "http://localhost:8000/api/v1/agent/analysis/2330.TW",
    params={"agent_type": "openclaw"}
)

print(response.json())
```

### 2. Hermes Agent（DeepSeek V4 Pro）

#### 深度分析
```python
# 使用Hermes Agent進行深度分析
response = requests.post(
    "http://localhost:8000/api/v1/agent/chat",
    params={
        "message": "請提供台積電(2330.TW)的詳細技術分析和基本面分析",
        "agent_type": "hermes"
    }
)

print(response.json())
```

### 3. 自然語言查詢範例

#### 股票分析查詢
```
"請分析台積電(2330.TW)的投資價值"
"請預測台積電未來一個月的股價走勢"
"請比較台積電和聯發科的投資價值"
"請提供台灣半導體產業的分析報告"
```

#### 投資建議查詢
```
"我有100萬台幣，請建議投資組合"
"請評估台積電的風險等級"
"請提供低風險的投資建議"
"請分析台灣股市的整體趨勢"
```

#### 國際市場查詢
```
"請分析台灣股市與美國股市的連動性"
"請比較台灣、日本、韓國股市的表現"
"請預測國際股市對台灣股市的影響"
```

---

## 券商API整合

### 1. 永豐金證券Shioaji API

#### 配置步驟
1. 開立永豐金證券帳戶
2. 申請Shioaji API權限
3. 獲取API密鑰和密鑰
4. 配置到 `.env` 文件

#### 使用範例
```python
import requests

# 獲取帳戶資訊
response = requests.get(
    "http://localhost:8000/api/v1/broker/accounts",
    params={"broker": "shioaji"}
)

# 下單購買
response = requests.post(
    "http://localhost:8000/api/v1/broker/order",
    params={
        "stock_id": "2330.TW",
        "action": "buy",
        "quantity": 1000,
        "price": 600.0,
        "broker": "shioaji"
    }
)
```

### 2. 富邦證券API

#### 配置步驟
1. 開立富邦證券帳戶
2. 申請API權限
3. 獲取API密鑰
4. 配置到 `.env` 文件

#### 使用範例
```python
import requests

# 獲取帳戶資訊
response = requests.get(
    "http://localhost:8000/api/v1/broker/accounts",
    params={"broker": "fubon"}
)

# 下單購買
response = requests.post(
    "http://localhost:8000/api/v1/broker/order",
    params={
        "stock_id": "2330.TW",
        "action": "buy",
        "quantity": 1000,
        "price": 600.0,
        "broker": "fubon"
    }
)
```

### 3. 券商API比較

| 券商 | API | 免費 | 即時報價 | 下單功能 | 開戶要求 |
|------|-----|------|----------|----------|----------|
| 永豐金證券 | Shioaji | ✓ | ✓ | ✓ | 需開戶 |
| 富邦證券 | Fubon API | ✓ | ✓ | ✓ | 需開戶 |
| 元大證券 | Yuanta API | ✓ | ✓ | ✓ | 需開戶 |
| 凱基證券 | KGI API | ✓ | ✓ | ✓ | 需開戶 |

---

## 常見問題解答

### 1. 安裝問題

#### Q: 安裝依賴時出現錯誤
A: 確保使用Python 3.9+，並建議使用虛擬環境：
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Q: 無法連接到資料庫
A: 檢查PostgreSQL服務是否運行，並確認資料庫連接資訊：
```bash
sudo systemctl status postgresql
psql -U stock_user -d stock_analysis
```

### 2. API使用問題

#### Q: 獲取股票數據失敗
A: 檢查股票代碼格式是否正確（例如：2330.TW），並確保網路連接正常。

#### Q: 技術分析指標計算錯誤
A: 確保有足夠的歷史數據，某些指標需要至少20天以上的數據。

### 3. 券商API問題

#### Q: 無法連接到券商API
A: 檢查API密鑰是否正確，並確保已開立券商帳戶。

#### Q: 下單失敗
A: 檢查帳戶餘額是否足夠，並確認股票代碼和價格是否正確。

### 4. AI Agent問題

#### Q: AI Agent回應緩慢
A: 這是正常的，AI模型需要時間處理。可以調整超時時間或使用更快的模型。

#### Q: AI Agent回應不準確
A: AI模型的回應僅供參考，投資決策請結合多方面分析。

### 5. 性能優化

#### Q: API回應緩慢
A: 啟用Redis快取，並調整快取過期時間：
```env
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
```

#### Q: 記憶體使用過高
A: 減少同時處理的股票數量，並調整資料更新頻率：
```env
DATA_UPDATE_INTERVAL=3600
```

---

## 進階功能

### 1. 自定義技術指標

```python
# 在analysis/technical_analysis.py中添加自定義指標
def _calculate_custom_indicator(self, df: pd.DataFrame) -> Dict:
    """計算自定義指標"""
    # 您的自定義計算邏輯
    pass
```

### 2. 自定義估值模型

```python
# 在analysis/valuation_analysis.py中添加自定義估值模型
def _calculate_custom_valuation(self, financial_data: Dict, realtime_data: Dict) -> Dict:
    """計算自定義估值模型"""
    # 您的自定義估值邏輯
    pass
```

### 3. 自定義AI Agent

```python
# 在agents目錄中添加自定義AI Agent
class CustomAgent:
    def __init__(self):
        # 初始化配置
        pass
    
    async def chat(self, message: str) -> Dict:
        """自定義對話邏輯"""
        # 您的自定義對話邏輯
        pass
```

### 4. 整合其他資料來源

```python
# 在data/data_fetcher.py中添加自定義資料來源
async def get_custom_data(self, stock_id: str) -> Dict:
    """獲取自定義資料來源"""
    # 您的自定義資料取得邏輯
    pass
```

---

## 部署指南

### 1. Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://stock_user:password@db:5432/stock_analysis
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=stock_analysis
      - POSTGRES_USER=stock_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. 雲端部署

#### Google Cloud Run
```bash
# 部署到Google Cloud Run
gcloud run deploy stock-analysis \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated
```

#### AWS Lambda
```bash
# 使用Serverless框架部署
serverless deploy
```

### 3. 本地部署

```bash
# 啟動服務
python main.py

# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 監控與維護

### 1. 日誌監控

```bash
# 查看應用日誌
tail -f logs/app.log

# 查看錯誤日誌
grep -i error logs/app.log
```

### 2. 性能監控

```bash
# 監控API回應時間
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/stocks/2330.TW/realtime"

# 監控系統資源
top
htop
```

### 3. 資料備份

```bash
# 備份PostgreSQL資料庫
pg_dump -U stock_user stock_analysis > backup.sql

# 備份Redis資料
redis-cli BGSAVE
```

---

## 更新與升級

### 1. 更新依賴

```bash
# 更新所有依賴
pip install --upgrade -r requirements.txt

# 更新特定套件
pip install --upgrade yfinance
```

### 2. 升級應用

```bash
# 拉取最新代碼
git pull origin main

# 重新安裝依賴
pip install -r requirements.txt

# 重啟服務
python main.py
```

### 3. 資料庫遷移

```bash
# 如果有資料庫結構變更
alembic upgrade head
```

---

## 技術支援

### 1. 問題回報
- GitHub Issues：提交技術問題
- 電子郵件：聯繫開發團隊

### 2. 文檔資源
- API文檔：http://localhost:8000/docs
- 技術文檔：docs/目錄
- 範例代碼：examples/目錄

### 3. 社群支援
- GitHub Discussions：討論區
- Discord：即時聊天
- Stack Overflow：技術問答

---

## 免責聲明

本工具僅供學習和研究使用，不構成投資建議。投資有風險，入市需謹慎。使用本工具進行投資決策時，請自行承擔風險。

---

## 授權條款

MIT License - 詳見LICENSE文件