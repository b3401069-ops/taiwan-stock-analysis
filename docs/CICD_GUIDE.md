# 🔄 CI/CD 指南 - GitHub Actions

## 📋 目錄

1. [CI/CD 概述](#cicd-概述)
2. [GitHub Actions 工作流程](#github-actions-工作流程)
3. [測試自動化](#測試自動化)
4. [程式碼品質檢查](#程式碼品質檢查)
5. [安全性檢查](#安全性檢查)
6. [建置與部署](#建置與部署)
7. [最佳實踐](#最佳實踐)

---

## 🎯 CI/CD 概述

本專案使用 **GitHub Actions** 進行持續整合和持續部署 (CI/CD)，確保程式碼品質和自動化部署。

### 工作流程

```
程式碼提交 → 自動測試 → 程式碼品質檢查 → 安全性檢查 → 建置 → 部署
```

### 主要功能

| 功能 | 說明 |
|------|------|
| **自動測試** | 每次提交自動執行單元測試 |
| **覆蓋率報告** | 自動產生測試覆蓋率報告 |
| **程式碼品質** | 使用 flake8、black、isort 檢查程式碼 |
| **類型檢查** | 使用 mypy 進行類型檢查 |
| **安全性檢查** | 使用 bandit、safety 檢查安全性問題 |
| **自動建置** | 自動建置 Python 套件 |
| **自動部署** | 自動部署到 PyPI |

---

## 🚀 GitHub Actions 工作流程

### 工作流程檔案

```yaml
.github/workflows/test.yml
```

### 工作流程結構

```yaml
name: Tests

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    # 執行測試
    
  lint:
    # 程式碼品質檢查
    
  security:
    # 安全性檢查
    
  build:
    # 建置套件
    
  deploy:
    # 部署到 PyPI
```

### 觸發條件

| 條件 | 說明 |
|------|------|
| `push` | 推送到 main 或 master 分支時觸發 |
| `pull_request` | 建立或更新 PR 時觸發 |

---

## 🧪 測試自動化

### 測試矩陣

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']
```

### 測試步驟

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing
```

### 覆蓋率報告

```yaml
- name: Upload coverage to Codecov
  if: matrix.python-version == '3.11'
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: false
```

### 本地執行測試

```bash
# 執行所有測試
pytest tests/ -v

# 執行測試並產生覆蓋率報告
pytest tests/ --cov=. --cov-report=term-missing

# 執行特定測試
pytest tests/test_indicators.py -v

# 執行效能測試
pytest tests/test_performance.py -v -m slow
```

---

## 🔍 程式碼品質檢查

### Linting 工具

| 工具 | 用途 | 說明 |
|------|------|------|
| **flake8** | 靜態分析 | 檢查程式碼風格和錯誤 |
| **black** | 格式化 | 自動格式化程式碼 |
| **isort** | 匯入排序 | 排序 import 語句 |
| **mypy** | 類型檢查 | 靜態類型檢查 |

### 檢查步驟

```yaml
- name: Run linting
  run: |
    # 檢查嚴重錯誤
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    # 檢查程式碼風格
    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    # 檢查格式
    black --check .
    
    # 檢查匯入
    isort --check-only .
```

### 本地執行檢查

```bash
# 安裝工具
pip install flake8 black isort mypy

# 執行 flake8
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 執行 black
black --check .

# 執行 isort
isort --check-only .

# 執行 mypy
mypy . --ignore-missing-imports
```

### 自動格式化

```bash
# 使用 black 格式化
black .

# 使用 isort 排序匯入
isort .
```

---

## 🔒 安全性檢查

### 安全性工具

| 工具 | 用途 | 說明 |
|------|------|------|
| **bandit** | 安全性掃描 | 檢查程式碼安全性問題 |
| **safety** | 依賴檢查 | 檢查已知漏洞的依賴 |

### 檢查步驟

```yaml
- name: Run security checks
  run: |
    # 檢查安全性問題
    bandit -r . -ll -ii
    
    # 檢查有漏洞的依賴
    safety check
```

### 本地執行檢查

```bash
# 安裝工具
pip install bandit safety

# 執行安全性掃描
bandit -r . -ll -ii

# 執行依賴檢查
safety check
```

### 常見安全性問題

1. **SQL 注入**: 使用參數化查詢
2. **XSS 攻擊**: 轉義使用者輸入
3. **硬編碼密碼**: 使用環境變數
4. **不安全的反序列化**: 避免使用 pickle

---

## 🏗️ 建置與部署

### 建置步驟

```yaml
- name: Build package
  run: |
    python -m build
```

### 上傳產物

```yaml
- name: Upload build artifacts
  uses: actions/upload-artifact@v3
  with:
    name: package
    path: dist/
```

### 部署到 PyPI

```yaml
- name: Publish to PyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  run: |
    twine upload dist/*
```

### 本地建置

```bash
# 安裝建置工具
pip install build twine

# 建置套件
python -m build

# 檢查套件
twine check dist/*

# 上傳到 TestPyPI
twine upload --repository testpypi dist/*
```

---

## 📊 最佳實踐

### 1. 工作流程設計

```yaml
# 使用矩陣測試多個 Python 版本
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']

# 快取依賴
- name: Cache pip
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### 2. 測試策略

```yaml
# 分離快速測試和慢速測試
- name: Run fast tests
  run: pytest tests/ -v -m "not slow"

- name: Run slow tests
  run: pytest tests/ -v -m slow
```

### 3. 安全性最佳實踐

```yaml
# 使用 secrets
env:
  PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}

# 限制權限
permissions:
  contents: read
  packages: write
```

### 4. 監控與通知

```yaml
# 建立失敗時通知
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Tests failed!'
```

---

## 🔧 本地開發設定

### 安裝開發依賴

```bash
# 安裝所有依賴
pip install -r requirements.txt

# 安裝開發工具
pip install pytest pytest-cov flake8 black isort mypy bandit safety
```

### Pre-commit Hooks

建立 `.pre-commit-config.yaml`:

```yaml
repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: trailing-whitespace
  - id: end-of-file-fixer
  - id: check-yaml
  - id: check-added-large-files

- repo: https://github.com/psf/black
  rev: 23.3.0
  hooks:
  - id: black

- repo: https://github.com/pycqa/isort
  rev: 5.12.0
  hooks:
  - id: isort

- repo: https://github.com/pycqa/flake8
  rev: 6.0.0
  hooks:
  - id: flake8
```

安裝 pre-commit:

```bash
pip install pre-commit
pre-commit install
```

### 本地執行完整檢查

```bash
# 執行所有檢查
pre-commit run --all-files

# 或手動執行
black .
isort .
flake8 .
pytest tests/ -v --cov=.
```

---

## 📈 覆蓋率報告

### 本地產生報告

```bash
# 終端機報告
pytest tests/ --cov=. --cov-report=term-missing

# HTML 報告
pytest tests/ --cov=. --cov-report=html

# XML 報告
pytest tests/ --cov=. --cov-report=xml
```

### 查看報告

```bash
# 開啟 HTML 報告
open htmlcov/index.html

# 或使用瀏覽器開啟
python -m http.server 8080
# 然後訪問 http://localhost:8080/htmlcov/
```

### Codecov 整合

1. 註冊 [Codecov](https://codecov.io/)
2. 連結 GitHub 倉庫
3. 在 GitHub Actions 中上傳覆蓋率報告
4. 在 Codecov 查看覆蓋率趨勢

---

## 🚨 常見問題

### Q: 測試在本地通過但在 CI 失敗

**可能原因**:
- 環境差異（Python 版本、作業系統）
- 依賴版本不同
- 環境變數缺失

**解決方案**:
```bash
# 使用與 CI 相同的 Python 版本
python3.11 -m pytest tests/

# 檢查依賴版本
pip freeze > requirements-ci.txt
diff requirements.txt requirements-ci.txt
```

### Q: 覆蓋率報告不準確

**可能原因**:
- 測試未涵蓋所有程式碼
- 排除檔案設定不正確

**解決方案**:
```bash
# 檢查排除設定
pytest tests/ --cov=. --cov-report=term-missing | grep "Missing"

# 更新排除設定
# pytest.ini
[tool:pytest]
addopts = --cov=. --cov-config=.coveragerc
```

### Q: GitHub Actions 執行時間過長

**可能原因**:
- 測試太多
- 依賴安裝慢

**解決方案**:
```yaml
# 快取依賴
- name: Cache pip
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

# 分離測試
- name: Run fast tests
  run: pytest tests/ -v -m "not slow"
```

---

## 📚 相關資源

- [GitHub Actions 官方文件](https://docs.github.com/en/actions)
- [pytest 官方文件](https://docs.pytest.org/)
- [Codecov 官方文件](https://docs.codecov.io/)
- [flake8 官方文件](https://flake8.pycqa.org/)
- [black 官方文件](https://black.readthedocs.io/)

---

**最後更新**: 2026-07-01
**維護者**: OpenHands Agent
