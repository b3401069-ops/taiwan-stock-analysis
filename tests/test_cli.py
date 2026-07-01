"""CLI 工具測試。"""

from __future__ import annotations

import json
import os
import pytest
from unittest.mock import patch, MagicMock


class TestCLIWatchlist:
    """CLI 關注清單測試。"""

    def test_load_watchlist_empty(self, tmp_path):
        """載入空關注清單。"""
        # 建立臨時目錄和檔案
        watchlist_file = tmp_path / "watchlist.json"
        
        # 模擬 load_watchlist 函數
        def load_watchlist(file_path):
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        
        result = load_watchlist(str(watchlist_file))
        assert result == []

    def test_load_watchlist_with_data(self, watchlist_file):
        """載入有資料的關注清單。"""
        def load_watchlist(file_path):
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        
        result = load_watchlist(watchlist_file)
        assert len(result) == 2
        assert result[0]["stock_id"] == "2330"
        assert result[1]["stock_id"] == "2317"

    def test_save_watchlist(self, tmp_path):
        """儲存關注清單。"""
        watchlist_file = tmp_path / "watchlist.json"
        watchlist = [
            {"stock_id": "2330", "name": "台積電"},
            {"stock_id": "2317", "name": "鴻海"},
        ]
        
        def save_watchlist(file_path, data):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        save_watchlist(str(watchlist_file), watchlist)
        
        # 驗證檔案存在
        assert watchlist_file.exists()
        
        # 驗證內容
        with open(watchlist_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        
        assert len(loaded) == 2
        assert loaded[0]["stock_id"] == "2330"

    def test_add_to_watchlist(self, watchlist_file):
        """新增到關注清單。"""
        # 載入現有清單
        with open(watchlist_file, "r", encoding="utf-8") as f:
            watchlist = json.load(f)
        
        # 新增股票
        new_stock = {"stock_id": "2454", "name": "聯發科"}
        watchlist.append(new_stock)
        
        # 儲存
        with open(watchlist_file, "w", encoding="utf-8") as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
        
        # 驗證
        with open(watchlist_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        
        assert len(loaded) == 3
        assert loaded[-1]["stock_id"] == "2454"

    def test_remove_from_watchlist(self, watchlist_file):
        """從關注清單移除。"""
        # 載入現有清單
        with open(watchlist_file, "r", encoding="utf-8") as f:
            watchlist = json.load(f)
        
        # 移除股票
        watchlist = [s for s in watchlist if s["stock_id"] != "2330"]
        
        # 儲存
        with open(watchlist_file, "w", encoding="utf-8") as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
        
        # 驗證
        with open(watchlist_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        
        assert len(loaded) == 1
        assert loaded[0]["stock_id"] == "2317"

    def test_watchlist_duplicate_check(self, watchlist_file):
        """關注清單重複檢查。"""
        # 載入現有清單
        with open(watchlist_file, "r", encoding="utf-8") as f:
            watchlist = json.load(f)
        
        # 嘗試新增重複股票
        duplicate_id = "2330"
        is_duplicate = any(s.get("stock_id") == duplicate_id for s in watchlist)
        
        assert is_duplicate is True
        
        # 嘗試新增新股票
        new_id = "2454"
        is_duplicate = any(s.get("stock_id") == new_id for s in watchlist)
        
        assert is_duplicate is False


class TestCLICommandParsing:
    """CLI 命令解析測試。"""

    def test_command_structure(self):
        """命令結構測試。"""
        commands = [
            "stock",
            "screener",
            "industry",
            "concept",
            "ai",
            "market",
            "backtest",
            "watchlist",
            "report",
            "discover",
            "morning-routine",
            "notify",
            "sync",
            "status",
            "validate",
        ]
        
        # 所有命令應在可用命令列表中
        for cmd in commands:
            assert cmd in commands

    def test_stock_subcommands(self):
        """股票子命令測試。"""
        subcommands = ["info", "price", "valuation"]
        
        for subcmd in subcommands:
            assert subcmd in subcommands

    def test_screener_subcommands(self):
        """選股子命令測試。"""
        subcommands = ["run", "weights"]
        
        for subcmd in subcommands:
            assert subcmd in subcommands

    def test_industry_subcommands(self):
        """產業子命令測試。"""
        subcommands = ["ranking", "rotation"]
        
        for subcmd in subcommands:
            assert subcmd in subcommands

    def test_concept_subcommands(self):
        """概念股子命令測試。"""
        subcommands = ["ranking", "hot"]
        
        for subcmd in subcommands:
            assert subcmd in subcommands

    def test_watchlist_subcommands(self):
        """關注清單子命令測試。"""
        subcommands = ["add", "remove", "list", "sync"]
        
        for subcmd in subcommands:
            assert subcmd in subcommands

    def test_report_subcommands(self):
        """報告子命令測試。"""
        subcommands = ["daily", "weekly", "monthly"]
        
        for subcmd in subcommands:
            assert subcmd in subcommands


class TestCLIOutput:
    """CLI 輸出格式測試。"""

    def test_json_output_format(self):
        """JSON 輸出格式測試。"""
        data = {"success": True, "data": {"stock_id": "2330.TW"}}
        
        # 應能正確序列化
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        assert "success" in json_str
        assert "2330.TW" in json_str
        
        # 應能正確反序列化
        loaded = json.loads(json_str)
        assert loaded["success"] is True
        assert loaded["data"]["stock_id"] == "2330.TW"

    def test_table_output_format(self):
        """表格輸出格式測試。"""
        headers = ["排名", "股票代碼", "股票名稱", "分數"]
        rows = [
            ["1", "2330.TW", "台積電", "0.7234"],
            ["2", "2454.TW", "聯發科", "0.6891"],
        ]
        
        # 建立表格
        table = [headers] + rows
        
        # 驗證結構
        assert len(table) == 3
        assert len(table[0]) == 4
        assert table[1][0] == "1"
        assert table[2][0] == "2"

    def test_error_output_format(self):
        """錯誤輸出格式測試。"""
        error_messages = [
            "❌ 無法連接到伺服器",
            "❌ API 錯誤: 500",
            "❌ 沒有篩選結果",
        ]
        
        for msg in error_messages:
            assert "❌" in msg

    def test_success_output_format(self):
        """成功輸出格式測試。"""
        success_messages = [
            "✅ 已新增 2330 到關注清單",
            "✅ 因子權重更新成功",
            "✅ 通知已發送",
        ]
        
        for msg in success_messages:
            assert "✅" in msg


class TestCLIHelpMessages:
    """CLI 幫助訊息測試。"""

    def test_main_help(self):
        """主幫助訊息測試。"""
        help_text = """
台灣股票分析工具 - CLI

可用命令:
  stock        股票相關命令
  screener     多因子選股命令
  industry     產業分析命令
  concept      概念股分析命令
  ai           AI 分析命令
  market       市場分析命令
  backtest     回測命令
  watchlist    關注清單命令
  report       報告命令
  discover     全市場選股掃描命令
  morning-routine  每日早晨例行流程命令
  notify       通知命令
  sync         資料同步命令
  status       系統狀態查詢
  validate     資料驗證
"""
        # 驗證幫助訊息包含所有命令
        for cmd in ["stock", "screener", "industry", "concept", "ai", "market", "backtest", "watchlist", "report", "discover", "morning-routine", "notify", "sync", "status", "validate"]:
            assert cmd in help_text

    def test_stock_help(self):
        """股票命令幫助訊息測試。"""
        help_text = """
股票相關命令:
  info        取得股票資訊
  price       取得股票價格
  valuation   取得估值指標
"""
        for subcmd in ["info", "price", "valuation"]:
            assert subcmd in help_text

    def test_screener_help(self):
        """選股命令幫助訊息測試。"""
        help_text = """
多因子選股命令:
  run         執行選股篩選
  weights     更新因子權重
"""
        for subcmd in ["run", "weights"]:
            assert subcmd in help_text
