#!/usr/bin/env python3
"""
台灣股票分析工具 - CLI 工具
提供命令列介面，方便自動化操作
參考 taiwan-quant-project 的 cli.py

Usage:
    # 股票相關
    python cli.py stock info 2330.TW
    python cli.py stock price 2330.TW --period 6mo
    python cli.py stock valuation 2330.TW

    # 多因子選股
    python cli.py screener run --top-n 10
    python cli.py screener weights --momentum 0.3

    # 產業分析
    python cli.py industry ranking --period 6mo
    python cli.py industry rotation --period 6mo

    # 概念股分析
    python cli.py concept ranking --period 6mo
    python cli.py concept hot --min-heat 0.6

    # AI 分析
    python cli.py ai summary --top-n 10

    # 市場分析
    python cli.py market regime

    # 回測
    python cli.py backtest walk-forward 2330.TW rsi_oversold

    # 關注清單管理
    python cli.py watchlist add 2330 --name 台積電
    python cli.py watchlist remove 2330
    python cli.py watchlist list
    python cli.py watchlist sync

    # 每日報告
    python cli.py report daily --top 10 --notify
    python cli.py report weekly --notify
    python cli.py report monthly --notify

    # 全市場選股掃描
    python cli.py discover --top 20 --min-price 50
    python cli.py discover --export picks.csv --notify

    # 每日早晨例行流程
    python cli.py morning-routine --notify
    python cli.py morning-routine --skip-sync --notify
    python cli.py morning-routine --dry-run

    # 通知
    python cli.py notify --message "測試訊息"
    python cli.py notify --stock-alert 2330.TW --type 停損警報 --message "跌破支撐"

    # 資料同步
    python cli.py sync --stocks 2330 2317
    python cli.py sync --start 2023-01-01 --end 2024-12-31

    # 資料查詢
    python cli.py status
    python cli.py validate
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

# API 基礎 URL
API_BASE = "http://localhost:9999/api/v1"

# 關注清單檔案
WATCHLIST_FILE = "data/watchlist.json"


def call_api(
    endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None
) -> Optional[Dict]:
    """調用 API"""
    try:
        url = f"{API_BASE}{endpoint}"

        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, params=params, json=data, timeout=30)
        else:
            print(f"❌ 不支援的 HTTP 方法: {method}")
            return None

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API 錯誤: {response.status_code}")
            print(f"   {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到伺服器，請確認伺服器是否啟動")
        return None
    except Exception as e:
        print(f"❌ API 調用失敗: {e}")
        return None


def print_json(data: Dict, indent: int = 2):
    """列印 JSON 資料"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def load_watchlist() -> List[Dict]:
    """載入關注清單"""
    try:
        if os.path.exists(WATCHLIST_FILE):
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 載入關注清單失敗: {e}")
    return []


def save_watchlist(watchlist: List[Dict]):
    """儲存關注清單"""
    try:
        os.makedirs(os.path.dirname(WATCHLIST_FILE), exist_ok=True)
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(watchlist, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ 儲存關注清單失敗: {e}")


# ──────────────────────────────────────────────
#  股票相關命令
# ──────────────────────────────────────────────
def stock_command(args):
    """股票相關命令"""
    if args.stock_action == "info":
        result = call_api(f"/stock/{args.stock_id}")
        if result and result.get("success"):
            print(f"\n📊 股票資訊: {args.stock_id}")
            print("=" * 50)
            print_json(result["data"])
        else:
            print(f"❌ 無法取得 {args.stock_id} 的資訊")

    elif args.stock_action == "price":
        result = call_api(f"/price/{args.stock_id}?period={args.period}")
        if result and result.get("success"):
            print(f"\n📈 股票價格: {args.stock_id}")
            print("=" * 50)
            print(f"期間: {result['data']['period']}")
            print(f"資料筆數: {len(result['data']['data'])}")

            # 顯示摘要
            summary = result["data"]["summary"]
            print(f"\n摘要:")
            print(f"  開始日期: {summary['start_date']}")
            print(f"  結束日期: {summary['end_date']}")
            print(f"  最新價格: {summary['latest_price']:.2f}")
            print(f"  最高價格: {summary['highest_price']:.2f}")
            print(f"  最低價格: {summary['lowest_price']:.2f}")
            print(f"  平均價格: {summary['average_price']:.2f}")
        else:
            print(f"❌ 無法取得 {args.stock_id} 的價格")

    elif args.stock_action == "valuation":
        result = call_api(f"/valuation/{args.stock_id}")
        if result and result.get("success"):
            print(f"\n💰 估值指標: {args.stock_id}")
            print("=" * 50)

            valuation = result["data"]
            print(f"目前價格: {valuation['current_price']:.2f}")
            print(f"本益比 (PE): {valuation['pe_ratio']:.2f}")
            print(f"股價淨值比 (PB): {valuation['pb_ratio']:.2f}")
            print(f"股利殖利率: {valuation['dividend_yield']:.2f}%")
            print(f"估值評級: {valuation['valuation_rating']}")
        else:
            print(f"❌ 無法取得 {args.stock_id} 的估值")


# ──────────────────────────────────────────────
#  多因子選股命令
# ──────────────────────────────────────────────
def screener_command(args):
    """多因子選股命令"""
    if args.screener_action == "run":
        print("\n🔍 多因子選股篩選")
        print("=" * 50)

        result = call_api(
            "/screener/multi-factor", method="POST", params={"top_n": args.top_n}
        )

        if result and result.get("success"):
            stocks = result["data"]

            if stocks:
                print(f"\n篩選結果 (前 {len(stocks)} 名):")
                print("-" * 50)

                for stock in stocks:
                    print(
                        f"{stock['rank']:2d}. {stock['stock_name']} ({stock['stock_id']})"
                    )
                    print(f"    綜合分數: {stock['composite_score']:.4f}")
                    print(f"    目前價格: {stock['details']['current_price']:.2f}")
                    print()
            else:
                print("❌ 沒有篩選結果")
        else:
            print("❌ 篩選失敗")

    elif args.screener_action == "weights":
        print("\n⚖️ 更新因子權重")
        print("=" * 50)

        weights = {
            "momentum": args.momentum,
            "value": args.value,
            "quality": args.quality,
            "size": args.size,
            "liquidity": args.liquidity,
            "institutional": args.institutional,
        }

        # 正規化權重
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        print(f"因子權重:")
        for factor, weight in weights.items():
            print(f"  {factor}: {weight:.2%}")

        result = call_api("/screener/weights", method="POST", data=weights)

        if result and result.get("success"):
            print("\n✅ 因子權重更新成功")
        else:
            print("\n❌ 因子權重更新失敗")


# ──────────────────────────────────────────────
#  產業分析命令
# ──────────────────────────────────────────────
def industry_command(args):
    """產業分析命令"""
    if args.industry_action == "ranking":
        print("\n🏭 產業強度排名")
        print("=" * 50)

        result = call_api(f"/industry/ranking?period={args.period}")

        if result and result.get("success"):
            ranking = result["data"]

            for item in ranking:
                print(f"{item['rank']:2d}. {item['industry']}")
                print(f"    強度分數: {item['strength_score']:.4f}")
                print(f"    信號: {item['signal']}")
                print(f"    20日動量: {item['momentum_20d']}")
                print()
        else:
            print("❌ 無法取得產業排名")

    elif args.industry_action == "rotation":
        print("\n🔄 產業輪動分析")
        print("=" * 50)

        result = call_api(f"/industry/rotation?period={args.period}")

        if result and result.get("success"):
            data = result["data"]

            # 顯示最強和最弱產業
            summary = data.get("summary", {})
            print(f"最強產業: {summary.get('strongest_industry', 'N/A')}")
            print(f"最弱產業: {summary.get('weakest_industry', 'N/A')}")
            print(f"輪動機會: {summary.get('total_opportunities', 0)} 個")

            # 顯示輪動機會
            opportunities = data.get("rotation_opportunities", [])
            if opportunities:
                print(f"\n輪動機會:")
                for opp in opportunities:
                    print(f"  • {opp['from_industry']} → {opp['to_industry']}")
                    print(f"    信號強度: {opp['signal_strength']:.2f}")
                    print(f"    預期報酬: {opp['expected_return']}")
                    print(f"    風險等級: {opp['risk_level']}")
                    print()
        else:
            print("❌ 無法取得產業輪動分析")


# ──────────────────────────────────────────────
#  概念股分析命令
# ──────────────────────────────────────────────
def concept_command(args):
    """概念股分析命令"""
    if args.concept_action == "ranking":
        print("\n💡 概念股熱度排名")
        print("=" * 50)

        result = call_api(f"/concept/ranking?period={args.period}")

        if result and result.get("success"):
            ranking = result["data"]

            for item in ranking:
                print(f"{item['rank']:2d}. {item['concept']}")
                print(f"    熱度分數: {item['heat_score']:.4f}")
                print(f"    趨勢: {item['trend']}")
                print(f"    20日動量: {item['avg_momentum_20d']}")
                print()
        else:
            print("❌ 無法取得概念股排名")

    elif args.concept_action == "hot":
        print("\n🔥 熱門概念股")
        print("=" * 50)

        result = call_api(f"/concept/hot?period={args.period}&min_heat={args.min_heat}")

        if result and result.get("success"):
            concepts = result["data"]

            if concepts:
                for concept in concepts:
                    print(
                        f"📌 {concept['concept']} (熱度: {concept['heat_score']:.2f})"
                    )
                    print(f"   描述: {concept['description']}")
                    print(f"   趨勢: {concept['trend']}")
                    print(f"   股票數: {len(concept['stocks'])}")
                    print()
            else:
                print("❌ 沒有熱門概念股")
        else:
            print("❌ 無法取得熱門概念股")


# ──────────────────────────────────────────────
#  AI 分析命令
# ──────────────────────────────────────────────
def ai_command(args):
    """AI 分析命令"""
    if args.ai_action == "summary":
        print("\n🤖 AI 選股摘要")
        print("=" * 50)

        result = call_api("/ai/summary", method="POST", params={"top_n": args.top_n})

        if result and result.get("success"):
            data = result["data"]

            # 執行摘要
            print("\n📋 執行摘要:")
            print(data.get("executive_summary", "N/A"))

            # 投資建議
            advice = data.get("investment_advice", {})
            print(f"\n💡 投資建議:")
            print(f"  • 市場建議: {advice.get('market_advice', 'N/A')}")
            print(f"  • 建議部位: {advice.get('position_size', 'N/A')}")
            print(f"  • 整體策略: {advice.get('overall_strategy', 'N/A')}")

            # 選股推薦
            recommendations = advice.get("stock_recommendations", [])
            if recommendations:
                print(f"\n⭐ 選股推薦:")
                for i, rec in enumerate(recommendations[:5]):
                    print(
                        f"  {i+1}. {rec['stock_name']} ({rec['stock_id']}) - 分數: {rec['composite_score']:.4f}"
                    )

            # 風險提示
            warnings = data.get("risk_warnings", [])
            if warnings:
                print(f"\n⚠️ 風險提示:")
                for warning in warnings:
                    print(f"  • {warning}")
        else:
            print("❌ AI 摘要生成失敗")


# ──────────────────────────────────────────────
#  市場分析命令
# ──────────────────────────────────────────────
def market_command(args):
    """市場分析命令"""
    if args.market_action == "regime":
        print("\n📊 市場狀態分析")
        print("=" * 50)

        result = call_api("/market/regime")

        if result and result.get("success"):
            data = result["data"]

            print(f"市場狀態: {data.get('regime_name', 'N/A')}")
            print(f"信心水平: {data.get('confidence', 0)}%")

            suggestion = data.get("suggestion", {})
            print(f"建議動作: {suggestion.get('action', 'N/A')}")
            print(f"分析原因: {suggestion.get('reason', 'N/A')}")
        else:
            print("❌ 無法取得市場狀態")


# ──────────────────────────────────────────────
#  回測命令
# ──────────────────────────────────────────────
def backtest_command(args):
    """回測命令"""
    if args.backtest_action == "walk-forward":
        print("\n🔄 Walk-Forward 驗證")
        print("=" * 50)

        result = call_api(
            "/backtest/walk-forward",
            method="POST",
            params={
                "stock_id": args.stock_id,
                "strategy_name": args.strategy,
                "train_window": args.train_window,
                "test_window": args.test_window,
                "step_size": args.step_size,
                "total_years": args.total_years,
            },
        )

        if result and result.get("success"):
            data = result["data"]

            print(f"股票代碼: {data.get('stock_id', 'N/A')}")
            print(f"策略名稱: {data.get('strategy_name', 'N/A')}")
            print(f"總期間數: {data.get('total_periods', 0)}")

            print(f"\n績效指標:")
            print(f"  • 平均報酬率: {data.get('avg_return', 'N/A')}")
            print(f"  • 平均最大回撤: {data.get('avg_max_drawdown', 'N/A')}")
            print(f"  • 平均勝率: {data.get('avg_win_rate', 'N/A')}")
            print(f"  • 平均夏普比率: {data.get('avg_sharpe_ratio', 'N/A')}")

            # 顯示整體指標
            overall = data.get("overall_metrics", {})
            if overall:
                print(f"\n整體指標:")
                print(f"  • 複合報酬率: {overall.get('compound_return', 'N/A')}")
                print(f"  • 報酬率穩定性: {overall.get('return_stability', 'N/A')}")
                print(
                    f"  • 風險調整後報酬: {overall.get('risk_adjusted_return', 'N/A')}"
                )
                print(f"  • 正報酬期間: {overall.get('positive_periods', 0)}")
                print(f"  • 負報酬期間: {overall.get('negative_periods', 0)}")
        else:
            print("❌ Walk-Forward 驗證失敗")


# ──────────────────────────────────────────────
#  關注清單命令
# ──────────────────────────────────────────────
def watchlist_command(args):
    """關注清單命令"""
    if args.watchlist_action == "add":
        print(f"\n➕ 新增關注股票: {args.stock_id}")
        print("=" * 50)

        watchlist = load_watchlist()

        # 檢查是否已存在
        for stock in watchlist:
            if stock.get("stock_id") == args.stock_id:
                print(f"⚠️ {args.stock_id} 已在關注清單中")
                return

        # 新增股票
        new_stock = {
            "stock_id": args.stock_id,
            "name": args.name or args.stock_id,
            "added_date": datetime.now().isoformat(),
            "notes": "",
        }

        watchlist.append(new_stock)
        save_watchlist(watchlist)

        print(f"✅ 已新增 {args.stock_id} 到關注清單")
        print(f"   名稱: {new_stock['name']}")

    elif args.watchlist_action == "remove":
        print(f"\n➖ 移除關注股票: {args.stock_id}")
        print("=" * 50)

        watchlist = load_watchlist()

        # 尋找並移除
        new_watchlist = [s for s in watchlist if s.get("stock_id") != args.stock_id]

        if len(new_watchlist) < len(watchlist):
            save_watchlist(new_watchlist)
            print(f"✅ 已從關注清單移除 {args.stock_id}")
        else:
            print(f"⚠️ {args.stock_id} 不在關注清單中")

    elif args.watchlist_action == "list":
        print("\n📋 關注清單")
        print("=" * 50)

        watchlist = load_watchlist()

        if watchlist:
            for i, stock in enumerate(watchlist, 1):
                print(
                    f"{i:2d}. {stock.get('stock_id', 'N/A')} - {stock.get('name', 'N/A')}"
                )
                print(f"    新增日期: {stock.get('added_date', 'N/A')}")
                if stock.get("notes"):
                    print(f"    備註: {stock['notes']}")
                print()
        else:
            print("關注清單為空")
            print("使用 'python cli.py watchlist add 2330 --name 台積電' 新增股票")

    elif args.watchlist_action == "sync":
        print("\n🔄 同步關注清單資料")
        print("=" * 50)

        watchlist = load_watchlist()

        if not watchlist:
            print("❌ 關注清單為空，請先新增股票")
            return

        print(f"正在同步 {len(watchlist)} 檔股票...")

        for stock in watchlist:
            stock_id = stock.get("stock_id", "")
            name = stock.get("name", "")

            # 呼叫同步 API
            result = call_api(f"/stock/{stock_id}?sync=true")

            if result and result.get("success"):
                print(f"✅ {stock_id} ({name}) 同步成功")
            else:
                print(f"❌ {stock_id} ({name}) 同步失敗")

        print("\n同步完成！")


# ──────────────────────────────────────────────
#  報告命令
# ──────────────────────────────────────────────
def report_command(args):
    """報告命令"""
    if args.report_action == "daily":
        print("\n📊 每日報告")
        print("=" * 50)

        # 取得 AI 選股摘要
        result = call_api("/ai/summary", method="POST", params={"top_n": args.top_n})

        if result and result.get("success"):
            data = result["data"]

            print("\n📋 執行摘要:")
            print(data.get("executive_summary", "N/A"))

            # 投資建議
            advice = data.get("investment_advice", {})
            print(f"\n💡 投資建議:")
            print(f"  • 市場建議: {advice.get('market_advice', 'N/A')}")
            print(f"  • 建議部位: {advice.get('position_size', 'N/A')}")
            print(f"  • 整體策略: {advice.get('overall_strategy', 'N/A')}")

            # 選股推薦
            recommendations = advice.get("stock_recommendations", [])
            if recommendations:
                print(f"\n⭐ 選股推薦:")
                for i, rec in enumerate(recommendations[:5]):
                    print(
                        f"  {i+1}. {rec['stock_name']} ({rec['stock_id']}) - 分數: {rec['composite_score']:.4f}"
                    )

            # 發送通知
            if args.notify:
                print("\n📱 發送通知...")
                call_api(
                    "/notification/discord/report",
                    method="POST",
                    params={"report_type": "每日報告"},
                )
                call_api(
                    "/notification/line/report",
                    method="POST",
                    params={"report_type": "每日報告"},
                )
                print("✅ 通知已發送")
        else:
            print("❌ 無法產生每日報告")

    elif args.report_action == "weekly":
        print("\n📊 每週報告")
        print("=" * 50)

        # 產業分析
        print("\n🏭 產業分析:")
        industry_result = call_api("/industry/ranking?period=1w")
        if industry_result and industry_result.get("success"):
            for item in industry_result["data"][:3]:
                print(
                    f"  • {item['industry']}: {item['strength_score']:.4f} ({item['signal']})"
                )

        # 概念股分析
        print("\n💡 概念股分析:")
        concept_result = call_api("/concept/ranking?period=1w")
        if concept_result and concept_result.get("success"):
            for item in concept_result["data"][:3]:
                print(
                    f"  • {item['concept']}: {item['heat_score']:.4f} ({item['trend']})"
                )

        # 發送通知
        if args.notify:
            print("\n📱 發送通知...")
            call_api(
                "/notification/discord/report",
                method="POST",
                params={"report_type": "每週報告"},
            )
            call_api(
                "/notification/line/report",
                method="POST",
                params={"report_type": "每週報告"},
            )
            print("✅ 通知已發送")

    elif args.report_action == "monthly":
        print("\n📊 每月報告")
        print("=" * 50)

        # 市場狀態
        print("\n📊 市場狀態:")
        market_result = call_api("/market/regime")
        if market_result and market_result.get("success"):
            data = market_result["data"]
            print(f"  • 市場狀態: {data.get('regime_name', 'N/A')}")
            print(f"  • 信心水平: {data.get('confidence', 0)}%")

        # 發送通知
        if args.notify:
            print("\n📱 發送通知...")
            call_api(
                "/notification/discord/report",
                method="POST",
                params={"report_type": "每月報告"},
            )
            call_api(
                "/notification/line/report",
                method="POST",
                params={"report_type": "每月報告"},
            )
            print("✅ 通知已發送")


# ──────────────────────────────────────────────
#  全市場選股掃描命令
# ──────────────────────────────────────────────
def discover_command(args):
    """全市場選股掃描命令"""
    print("\n🔍 全市場選股掃描")
    print("=" * 50)

    # 多因子選股
    result = call_api(
        "/screener/multi-factor", method="POST", params={"top_n": args.top_n}
    )

    if result and result.get("success"):
        stocks = result["data"]

        if stocks:
            print(f"\n篩選結果 (前 {len(stocks)} 名):")
            print("-" * 50)

            for stock in stocks:
                print(
                    f"{stock['rank']:2d}. {stock['stock_name']} ({stock['stock_id']})"
                )
                print(f"    綜合分數: {stock['composite_score']:.4f}")
                print(f"    目前價格: {stock['details']['current_price']:.2f}")
                print()

            # 匯出到 CSV
            if args.export:
                print(f"\n📁 匯出到: {args.export}")
                import csv

                with open(args.export, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["排名", "股票代碼", "股票名稱", "綜合分數", "目前價格"]
                    )

                    for stock in stocks:
                        writer.writerow(
                            [
                                stock["rank"],
                                stock["stock_id"],
                                stock["stock_name"],
                                stock["composite_score"],
                                stock["details"]["current_price"],
                            ]
                        )

                print(f"✅ 已匯出 {len(stocks)} 筆資料")

            # 發送通知
            if args.notify:
                print("\n📱 發送通知...")
                call_api(
                    "/notification/discord/report",
                    method="POST",
                    params={"report_type": "選股掃描結果"},
                )
                call_api(
                    "/notification/line/report",
                    method="POST",
                    params={"report_type": "選股掃描結果"},
                )
                print("✅ 通知已發送")
        else:
            print("❌ 沒有篩選結果")
    else:
        print("❌ 篩選失敗")


# ──────────────────────────────────────────────
#  每日早晨例行流程命令
# ──────────────────────────────────────────────
def morning_routine_command(args):
    """每日早晨例行流程命令"""
    print("\n🌅 每日早晨例行流程")
    print("=" * 50)

    start_time = datetime.now()
    steps_completed = 0

    # 步驟 1: 同步關注清單資料
    if not args.skip_sync:
        print("\n📥 步驟 1: 同步關注清單資料")
        watchlist = load_watchlist()

        if watchlist:
            for stock in watchlist:
                stock_id = stock.get("stock_id", "")
                result = call_api(f"/stock/{stock_id}?sync=true")
                if result and result.get("success"):
                    print(f"  ✅ {stock_id} 同步成功")
                else:
                    print(f"  ❌ {stock_id} 同步失敗")
        else:
            print("  ⚠️ 關注清單為空")

        steps_completed += 1
    else:
        print("\n⏭️ 步驟 1: 跳過同步")

    # 步驟 2: 市場狀態分析
    print("\n📊 步驟 2: 市場狀態分析")
    market_result = call_api("/market/regime")
    if market_result and market_result.get("success"):
        data = market_result["data"]
        print(f"  • 市場狀態: {data.get('regime_name', 'N/A')}")
        print(f"  • 信心水平: {data.get('confidence', 0)}%")
        steps_completed += 1
    else:
        print("  ❌ 市場狀態分析失敗")

    # 步驟 3: 產業輪動分析
    print("\n🏭 步驟 3: 產業輪動分析")
    industry_result = call_api("/industry/ranking?period=1d")
    if industry_result and industry_result.get("success"):
        for item in industry_result["data"][:3]:
            print(
                f"  • {item['industry']}: {item['strength_score']:.4f} ({item['signal']})"
            )
        steps_completed += 1
    else:
        print("  ❌ 產業輪動分析失敗")

    # 步驟 4: 概念股輪動分析
    print("\n💡 步驟 4: 概念股輪動分析")
    concept_result = call_api("/concept/ranking?period=1d")
    if concept_result and concept_result.get("success"):
        for item in concept_result["data"][:3]:
            print(f"  • {item['concept']}: {item['heat_score']:.4f} ({item['trend']})")
        steps_completed += 1
    else:
        print("  ❌ 概念股輪動分析失敗")

    # 步驟 5: AI 選股摘要
    print("\n🤖 步驟 5: AI 選股摘要")
    ai_result = call_api("/ai/summary", method="POST", params={"top_n": 10})
    if ai_result and ai_result.get("success"):
        data = ai_result["data"]
        advice = data.get("investment_advice", {})
        print(f"  • 市場建議: {advice.get('market_advice', 'N/A')}")
        print(f"  • 建議部位: {advice.get('position_size', 'N/A')}")
        steps_completed += 1
    else:
        print("  ❌ AI 選股摘要失敗")

    # 步驟 6: 發送通知
    if args.notify:
        print("\n📱 步驟 6: 發送通知")

        # 發送 Discord 通知
        call_api(
            "/notification/discord/report",
            method="POST",
            params={"report_type": "每日早晨報告"},
        )

        # 發送 Line 通知
        call_api(
            "/notification/line/report",
            method="POST",
            params={"report_type": "每日早晨報告"},
        )

        print("  ✅ 通知已發送")
        steps_completed += 1
    else:
        print("\n⏭️ 步驟 6: 跳過通知")

    # 完成摘要
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 50)
    print(f"✅ 每日早晨例行流程完成")
    print(f"   完成步驟: {steps_completed}/6")
    print(f"   執行時間: {duration:.1f} 秒")
    print("=" * 50)


# ──────────────────────────────────────────────
#  通知命令
# ──────────────────────────────────────────────
def notify_command(args):
    """通知命令"""
    if args.message:
        print(f"\n📱 發送通知")
        print("=" * 50)

        # 發送 Discord 通知
        call_api(
            "/notification/discord", method="POST", params={"content": args.message}
        )

        # 發送 Line 通知
        call_api("/notification/line", method="POST", params={"message": args.message})

        print("✅ 通知已發送")

    elif args.stock_alert:
        print(f"\n🚨 發送股票警報")
        print("=" * 50)

        stock_id = args.stock_alert
        alert_type = args.type or "一般警報"
        message = args.message or "股票異常"

        # 發送 Discord 警報
        call_api(
            "/notification/discord/stock-alert",
            method="POST",
            params={
                "stock_id": stock_id,
                "stock_name": stock_id,
                "alert_type": alert_type,
                "message": message,
            },
        )

        # 發送 Line 警報
        call_api(
            "/notification/line/stock-alert",
            method="POST",
            params={
                "stock_id": stock_id,
                "stock_name": stock_id,
                "alert_type": alert_type,
                "message": message,
            },
        )

        print("✅ 股票警報已發送")


# ──────────────────────────────────────────────
#  資料同步命令
# ──────────────────────────────────────────────
def sync_command(args):
    """資料同步命令"""
    print("\n🔄 資料同步")
    print("=" * 50)

    if args.stocks:
        # 同步指定股票
        print(f"正在同步 {len(args.stocks)} 檔股票...")

        for stock_id in args.stocks:
            result = call_api(f"/stock/{stock_id}?sync=true")
            if result and result.get("success"):
                print(f"✅ {stock_id} 同步成功")
            else:
                print(f"❌ {stock_id} 同步失敗")
    else:
        # 同步關注清單
        watchlist = load_watchlist()

        if watchlist:
            print(f"正在同步關注清單 ({len(watchlist)} 檔股票)...")

            for stock in watchlist:
                stock_id = stock.get("stock_id", "")
                result = call_api(f"/stock/{stock_id}?sync=true")
                if result and result.get("success"):
                    print(f"✅ {stock_id} 同步成功")
                else:
                    print(f"❌ {stock_id} 同步失敗")
        else:
            print("❌ 關注清單為空，請先新增股票")


# ──────────────────────────────────────────────
#  資料查詢命令
# ──────────────────────────────────────────────
def status_command(args):
    """資料查詢命令"""
    print("\n📊 系統狀態")
    print("=" * 50)

    # 檢查伺服器狀態
    result = call_api("/health")
    if result:
        print(f"✅ 伺服器狀態: 正常")
        print(f"   版本: {result.get('version', 'N/A')}")
        print(f"   資料庫: {result.get('database', 'N/A')}")
    else:
        print(f"❌ 伺服器狀態: 異常")

    # 關注清單統計
    watchlist = load_watchlist()
    print(f"\n📋 關注清單: {len(watchlist)} 檔股票")

    # 通知歷史統計
    history_result = call_api("/notification/history?limit=100")
    if history_result and history_result.get("success"):
        history = history_result["data"]
        print(f"📱 通知歷史: {len(history)} 筆")


def validate_command(args):
    """資料驗證命令"""
    print("\n🔍 資料驗證")
    print("=" * 50)

    watchlist = load_watchlist()

    if not watchlist:
        print("❌ 關注清單為空")
        return

    print(f"正在驗證 {len(watchlist)} 檔股票...")

    for stock in watchlist:
        stock_id = stock.get("stock_id", "")

        # 取得股票資料
        result = call_api(f"/stock/{stock_id}")

        if result and result.get("success"):
            data = result["data"]
            print(f"✅ {stock_id} - {data.get('name', 'N/A')}")
        else:
            print(f"❌ {stock_id} - 資料異常")


# ──────────────────────────────────────────────
#  主程式
# ──────────────────────────────────────────────
def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="台灣股票分析工具 - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 股票命令
    stock_parser = subparsers.add_parser("stock", help="股票相關命令")
    stock_subparsers = stock_parser.add_subparsers(dest="stock_action")

    # stock info
    stock_info_parser = stock_subparsers.add_parser("info", help="取得股票資訊")
    stock_info_parser.add_argument("stock_id", help="股票代碼")

    # stock price
    stock_price_parser = stock_subparsers.add_parser("price", help="取得股票價格")
    stock_price_parser.add_argument("stock_id", help="股票代碼")
    stock_price_parser.add_argument("--period", default="6mo", help="期間 (預設: 6mo)")

    # stock valuation
    stock_valuation_parser = stock_subparsers.add_parser(
        "valuation", help="取得估值指標"
    )
    stock_valuation_parser.add_argument("stock_id", help="股票代碼")

    # 多因子選股命令
    screener_parser = subparsers.add_parser("screener", help="多因子選股命令")
    screener_subparsers = screener_parser.add_subparsers(dest="screener_action")

    # screener run
    screener_run_parser = screener_subparsers.add_parser("run", help="執行選股篩選")
    screener_run_parser.add_argument(
        "--top-n", type=int, default=10, help="返回前 N 名"
    )

    # screener weights
    screener_weights_parser = screener_subparsers.add_parser(
        "weights", help="更新因子權重"
    )
    screener_weights_parser.add_argument(
        "--momentum", type=float, default=0.2, help="動量因子權重"
    )
    screener_weights_parser.add_argument(
        "--value", type=float, default=0.25, help="價值因子權重"
    )
    screener_weights_parser.add_argument(
        "--quality", type=float, default=0.25, help="品質因子權重"
    )
    screener_weights_parser.add_argument(
        "--size", type=float, default=0.1, help="規模因子權重"
    )
    screener_weights_parser.add_argument(
        "--liquidity", type=float, default=0.1, help="流動性因子權重"
    )
    screener_weights_parser.add_argument(
        "--institutional", type=float, default=0.1, help="法人因子權重"
    )

    # 產業分析命令
    industry_parser = subparsers.add_parser("industry", help="產業分析命令")
    industry_subparsers = industry_parser.add_subparsers(dest="industry_action")

    # industry ranking
    industry_ranking_parser = industry_subparsers.add_parser(
        "ranking", help="產業強度排名"
    )
    industry_ranking_parser.add_argument(
        "--period", default="6mo", help="期間 (預設: 6mo)"
    )

    # industry rotation
    industry_rotation_parser = industry_subparsers.add_parser(
        "rotation", help="產業輪動分析"
    )
    industry_rotation_parser.add_argument(
        "--period", default="6mo", help="期間 (預設: 6mo)"
    )

    # 概念股分析命令
    concept_parser = subparsers.add_parser("concept", help="概念股分析命令")
    concept_subparsers = concept_parser.add_subparsers(dest="concept_action")

    # concept ranking
    concept_ranking_parser = concept_subparsers.add_parser(
        "ranking", help="概念股熱度排名"
    )
    concept_ranking_parser.add_argument(
        "--period", default="6mo", help="期間 (預設: 6mo)"
    )

    # concept hot
    concept_hot_parser = concept_subparsers.add_parser("hot", help="熱門概念股")
    concept_hot_parser.add_argument("--period", default="6mo", help="期間 (預設: 6mo)")
    concept_hot_parser.add_argument(
        "--min-heat", type=float, default=0.5, help="最低熱度分數"
    )

    # AI 分析命令
    ai_parser = subparsers.add_parser("ai", help="AI 分析命令")
    ai_subparsers = ai_parser.add_subparsers(dest="ai_action")

    # ai summary
    ai_summary_parser = ai_subparsers.add_parser("summary", help="AI 選股摘要")
    ai_summary_parser.add_argument("--top-n", type=int, default=10, help="返回前 N 名")

    # 市場分析命令
    market_parser = subparsers.add_parser("market", help="市場分析命令")
    market_subparsers = market_parser.add_subparsers(dest="market_action")

    # market regime
    market_regime_parser = market_subparsers.add_parser("regime", help="市場狀態分析")

    # 回測命令
    backtest_parser = subparsers.add_parser("backtest", help="回測命令")
    backtest_subparsers = backtest_parser.add_subparsers(dest="backtest_action")

    # backtest walk-forward
    backtest_wf_parser = backtest_subparsers.add_parser(
        "walk-forward", help="Walk-Forward 驗證"
    )
    backtest_wf_parser.add_argument("stock_id", help="股票代碼")
    backtest_wf_parser.add_argument("strategy", help="策略名稱")
    backtest_wf_parser.add_argument(
        "--train-window", type=int, default=252, help="訓練窗口"
    )
    backtest_wf_parser.add_argument(
        "--test-window", type=int, default=63, help="測試窗口"
    )
    backtest_wf_parser.add_argument(
        "--step-size", type=int, default=21, help="步進大小"
    )
    backtest_wf_parser.add_argument(
        "--total-years", type=int, default=5, help="總回測年數"
    )

    # 關注清單命令
    watchlist_parser = subparsers.add_parser("watchlist", help="關注清單命令")
    watchlist_subparsers = watchlist_parser.add_subparsers(dest="watchlist_action")

    # watchlist add
    watchlist_add_parser = watchlist_subparsers.add_parser("add", help="新增關注股票")
    watchlist_add_parser.add_argument("stock_id", help="股票代碼")
    watchlist_add_parser.add_argument("--name", help="股票名稱")

    # watchlist remove
    watchlist_remove_parser = watchlist_subparsers.add_parser(
        "remove", help="移除關注股票"
    )
    watchlist_remove_parser.add_argument("stock_id", help="股票代碼")

    # watchlist list
    watchlist_subparsers.add_parser("list", help="顯示關注清單")

    # watchlist sync
    watchlist_subparsers.add_parser("sync", help="同步關注清單資料")

    # 報告命令
    report_parser = subparsers.add_parser("report", help="報告命令")
    report_subparsers = report_parser.add_subparsers(dest="report_action")

    # report daily
    report_daily_parser = report_subparsers.add_parser("daily", help="每日報告")
    report_daily_parser.add_argument(
        "--top-n", type=int, default=10, help="返回前 N 名"
    )
    report_daily_parser.add_argument("--notify", action="store_true", help="發送通知")

    # report weekly
    report_weekly_parser = report_subparsers.add_parser("weekly", help="每週報告")
    report_weekly_parser.add_argument("--notify", action="store_true", help="發送通知")

    # report monthly
    report_monthly_parser = report_subparsers.add_parser("monthly", help="每月報告")
    report_monthly_parser.add_argument("--notify", action="store_true", help="發送通知")

    # 全市場選股掃描命令
    discover_parser = subparsers.add_parser("discover", help="全市場選股掃描命令")
    discover_parser.add_argument("--top-n", type=int, default=20, help="返回前 N 名")
    discover_parser.add_argument("--min-price", type=float, help="最低價格")
    discover_parser.add_argument("--export", help="匯出到 CSV 檔案")
    discover_parser.add_argument("--notify", action="store_true", help="發送通知")

    # 每日早晨例行流程命令
    morning_parser = subparsers.add_parser(
        "morning-routine", help="每日早晨例行流程命令"
    )
    morning_parser.add_argument("--skip-sync", action="store_true", help="跳過同步")
    morning_parser.add_argument("--notify", action="store_true", help="發送通知")
    morning_parser.add_argument("--dry-run", action="store_true", help="預覽模式")

    # 通知命令
    notify_parser = subparsers.add_parser("notify", help="通知命令")
    notify_parser.add_argument("--message", help="訊息內容")
    notify_parser.add_argument("--stock-alert", help="股票警報")
    notify_parser.add_argument("--type", help="警報類型")

    # 資料同步命令
    sync_parser = subparsers.add_parser("sync", help="資料同步命令")
    sync_parser.add_argument("--stocks", nargs="+", help="指定股票代碼")
    sync_parser.add_argument("--start", help="開始日期")
    sync_parser.add_argument("--end", help="結束日期")

    # 資料查詢命令
    status_parser = subparsers.add_parser("status", help="系統狀態查詢")

    # 資料驗證命令
    validate_parser = subparsers.add_parser("validate", help="資料驗證")

    # 解析參數
    args = parser.parse_args()

    # 執行命令
    if args.command == "stock":
        stock_command(args)
    elif args.command == "screener":
        screener_command(args)
    elif args.command == "industry":
        industry_command(args)
    elif args.command == "concept":
        concept_command(args)
    elif args.command == "ai":
        ai_command(args)
    elif args.command == "market":
        market_command(args)
    elif args.command == "backtest":
        backtest_command(args)
    elif args.command == "watchlist":
        watchlist_command(args)
    elif args.command == "report":
        report_command(args)
    elif args.command == "discover":
        discover_command(args)
    elif args.command == "morning-routine":
        morning_routine_command(args)
    elif args.command == "notify":
        notify_command(args)
    elif args.command == "sync":
        sync_command(args)
    elif args.command == "status":
        status_command(args)
    elif args.command == "validate":
        validate_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
