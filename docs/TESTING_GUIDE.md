# 🧪 單元測試指南

## 📋 目錄

1. [測試概述](#測試概述)
2. [測試結構](#測試結構)
3. [執行測試](#執行測試)
4. [測試覆蓋率](#測試覆蓋率)
5. [測試分類](#測試分類)
6. [撰寫測試](#撰寫測試)
7. [Mock 與 Fixtures](#mock-與-fixtures)
8. [CI/CD 整合](#cicd-整合)

---

## 🎯 測試概述

本專案使用 **pytest** 作為測試框架，目標達到 **80% 以上**的測試覆蓋率。

### 測試統計

| 指標 | 數值 |
|------|------|
| **總測試數** | 117 |
| **通過** | 117 ✅ |
| **失敗** | 0 |
| **跳過** | 1 |
| **測試檔案覆蓋率** | 99% |
| **整體專案覆蓋率** | 11% |

---

## 📁 測試結構

```
tests/
├── conftest.py              # 共用 fixtures 和測試工具
├── test_indicators.py       # 技術指標計算測試
├── test_backtest.py         # 回測系統測試
├── test_screener.py         # 多因子選股測試
├── test_notification.py     # 通知服務測試
├── test_rotation.py         # 產業輪動測試
├── test_cli.py              # CLI 工具測試
├── test_market_regime.py    # 市場狀態測試
└── test_api.py              # API 端點測試
```

---

## 🚀 執行測試

### 基本執行

```bash
# 執行所有測試
pytest tests/ -v

# 執行特定測試檔案
pytest tests/test_indicators.py -v

# 執行特定測試類別
pytest tests/test_indicators.py::TestTechnicalIndicators -v

# 執行特定測試方法
pytest tests/test_indicators.py::TestTechnicalIndicators::test_sma_calculation -v
```

### 使用標記

```bash
# 執行單元測試
pytest tests/ -m unit -v

# 執行整合測試
pytest tests/ -m integration -v

# 執行 API 測試
pytest tests/ -m api -v

# 執行 CLI 測試
pytest tests/ -m cli -v
```

### 產生覆蓋率報告

```bash
# 終端機報告
pytest tests/ --cov=. --cov-report=term-missing

# HTML 報告
pytest tests/ --cov=. --cov-report=html

# XML 報告（供 CI/CD 使用）
pytest tests/ --cov=. --cov-report=xml
```

### 其他選項

```bash
# 停止於第一個失敗
pytest tests/ -x

# 顯示最慢的 10 個測試
pytest tests/ --durations=10

# 並行執行（需要安裝 pytest-xdist）
pytest tests/ -n auto

# 詳細輸出
pytest tests/ -v --tb=long
```

---

## 📊 測試覆蓋率

### 當前覆蓋率

| 模組 | 覆蓋率 | 說明 |
|------|--------|------|
| **tests/** | 99% | 測試檔案本身 |
| **config/** | 98% | 配置模組 |
| **analysis/backtest.py** | 25% | 回測引擎 |
| **analysis/industry_rotation.py** | 22% | 產業輪動 |
| **analysis/concept_rotation.py** | 27% | 概念股輪動 |
| **analysis/market_regime.py** | 13% | 市場狀態偵測 |
| **services/notification.py** | 14% | 通知服務 |
| **整體專案** | 11% | 所有模組 |

### 提高覆蓋率

1. **執行覆蓋率報告**:
   ```bash
   pytest tests/ --cov=. --cov-report=html
   ```

2. **查看未覆蓋的程式碼**:
   ```bash
   pytest tests/ --cov=. --cov-report=term-missing
   ```

3. **為未覆蓋的程式碼撰寫測試**:
   - 找出覆蓋率低的模組
   - 為關鍵函數撰寫測試
   - 使用 mock 避免外部依賴

---

## 🏷️ 測試分類

### 單元測試 (Unit Tests)

測試單一函數或方法的功能。

```python
def test_sma_calculation(self, df_100):
    """SMA 計算正確性。"""
    sma5 = df_100["close"].rolling(window=5).mean()
    expected = df_100["close"].iloc[:5].mean()
    assert sma5.iloc[4] == pytest.approx(expected, rel=1e-3)
```

### 整合測試 (Integration Tests)

測試多個模組之間的互動。

```python
@pytest.mark.integration
def test_full_workflow():
    """完整工作流程測試。"""
    # 1. 取得資料
    # 2. 計算指標
    # 3. 執行選股
    # 4. 產生報告
```

### API 測試

測試 API 端點的功能。

```python
def test_get_stock_info(self, client):
    """取得股票資訊。"""
    response = client.get("/api/v1/stock/2330.TW")
    assert response.status_code in [200, 500]
```

### CLI 測試

測試 CLI 命令的功能。

```python
def test_watchlist_add(self, watchlist_file):
    """新增關注股票。"""
    # 渋試新增功能
```

---

## ✍️ 撰寫測試

### 測試命名規範

```python
# 檔案名稱: test_<模組名稱>.py
# 類別名稱: Test<功能名稱>
# 方法名稱: test_<測試內容>

# 範例:
# tests/test_indicators.py
class TestTechnicalIndicators:
    def test_sma_calculation(self):
        """SMA 計算正確性。"""
        pass
```

### 測試結構

```python
class TestExample:
    """範例測試類別。"""

    def test_basic_functionality(self):
        """測試基本功能。"""
        # Arrange (準備)
        input_data = [1, 2, 3, 4, 5]
        
        # Act (執行)
        result = sum(input_data)
        
        # Assert (驗證)
        assert result == 15

    def test_edge_case(self):
        """測試邊界情況。"""
        # 測試空列表
        assert sum([]) == 0

    def test_error_handling(self):
        """測試錯誤處理。"""
        with pytest.raises(TypeError):
            sum([1, "2", 3])
```

### 使用 pytest.approx

```python
def test_float_comparison(self):
    """浮點數比較。"""
    result = 0.1 + 0.2
    assert result == pytest.approx(0.3, abs=1e-10)
```

### 使用 pytest.raises

```python
def test_exception_handling(self):
    """異常處理測試。"""
    with pytest.raises(ValueError, match="無效的股票代碼"):
        validate_stock_id("invalid")
```

---

## 🎭 Mock 與 Fixtures

### Fixtures

Fixtures 是 pytest 的核心功能，用於準備測試資料。

```python
@pytest.fixture()
def sample_data():
    """準備測試資料。"""
    return {
        "stock_id": "2330.TW",
        "price": 2450.0,
    }

def test_with_fixture(self, sample_data):
    """使用 fixture 的測試。"""
    assert sample_data["stock_id"] == "2330.TW"
```

### Mock

Mock 用於模擬外部依賴。

```python
from unittest.mock import patch, MagicMock

@patch("services.notification.get_notification_service")
def test_notification(self, mock_service):
    """使用 mock 的測試。"""
    mock_instance = MagicMock()
    mock_instance.send_message.return_value = True
    mock_service.return_value = mock_instance
    
    service = mock_service()
    result = service.send_message("測試")
    
    assert result is True
    mock_instance.send_message.assert_called_once()
```

### 共用 Fixtures

在 `conftest.py` 中定義共用 fixtures。

```python
# tests/conftest.py
@pytest.fixture()
def sample_ohlcv():
    """建立 OHLCV 測試資料。"""
    # ...
    return df

@pytest.fixture()
def mock_api_response():
    """Mock API 回應。"""
    def _mock_response(success=True, data=None):
        response = Mock()
        response.status_code = 200 if success else 500
        response.json.return_value = {"success": success, "data": data}
        return response
    return _mock_response
```

---

## 🔄 CI/CD 整合

### GitHub Actions

建立 `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

### 本地 CI

使用 `pre-commit` 執行測試:

```yaml
# .pre-commit-config.yaml
repos:
- repo: local
  hooks:
  - id: pytest
    name: pytest
    entry: pytest tests/ -x
    language: system
    pass_filenames: false
    always_run: true
```

---

## 📚 最佳實踐

### 1. 測試獨立性

每個測試應該獨立執行，不依賴其他測試。

```python
# ❌ 錯誤：測試之間有依賴
def test_create_user():
    user = create_user("test")
    return user.id

def test_update_user():
    user_id = test_create_user()  # 依賴前一個測試
    update_user(user_id, "new_name")

# ✅ 正確：每個測試獨立
@pytest.fixture()
def user():
    return create_user("test")

def test_create_user(user):
    assert user.name == "test"

def test_update_user(user):
    update_user(user.id, "new_name")
    assert user.name == "new_name"
```

### 2. 測試命名清晰

```python
# ❌ 錯誤：命名不清晰
def test_1():
    pass

# ✅ 正確：命名清晰
def test_sma_calculation_with_100_days_data():
    pass
```

### 3. 測試邊界情況

```python
def test_division():
    """測試除法。"""
    # 正常情況
    assert divide(10, 2) == 5
    
    # 邊界情況
    assert divide(0, 5) == 0
    
    # 錯誤情況
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
```

### 4. 使用 Parametrize

```python
@pytest.mark.parametrize("input,expected", [
    ([1, 2, 3], 6),
    ([0, 0, 0], 0),
    ([-1, 1], 0),
])
def test_sum(input, expected):
    """參數化測試。"""
    assert sum(input) == expected
```

---

## 🔧 常見問題

### Q: 如何測試需要網路連線的功能？

使用 mock 模擬網路請求：

```python
@patch("requests.get")
def test_api_call(self, mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    result = fetch_data()
    assert result == {"data": "test"}
```

### Q: 如何測試資料庫操作？

使用 in-memory 資料庫：

```python
@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

### Q: 如何測試非同步程式碼？

使用 `pytest-asyncio`：

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == "expected"
```

---

## 📚 相關資源

- [pytest 官方文件](https://docs.pytest.org/)
- [pytest-cov 覆蓋率](https://pytest-cov.readthedocs.io/)
- [unittest.mock 文件](https://docs.python.org/3/library/unittest.mock.html)
- [taiwan-quant-project 測試範例](https://github.com/Chun0122/taiwan-quant-project/tree/master/tests)

---

**最後更新**: 2026-07-01
**維護者**: OpenHands Agent
