#!/usr/bin/env python3
"""
台灣股票分析工具 - CLI 工具
提供命令列介面，方便自動化操作
參考 taiwan-quant-project 的 cli.py
"""
import argparse
import requests
import json
import sys
from typing import Dict, List, Optional
from datetime import datetime
import os

# API 基礎 URL
API_BASE = "http://localhost:9999/api/v1"


def call_api(endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Optional[Dict]:
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
            summary = result['data']['summary']
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


def screener_command(args):
    """多因子選股命令"""
    if args.screener_action == "run":
        print("\n🔍 多因子選股篩選")
        print("=" * 50)
        
        result = call_api("/screener/multi-factor", method="POST", params={"top_n": args.top_n})
        
        if result and result.get("success"):
            stocks = result["data"]
            
            if stocks:
                print(f"\n篩選結果 (前 {len(stocks)} 名):")
                print("-" * 50)
                
                for stock in stocks:
                    print(f"{stock['rank']:2d}. {stock['stock_name']} ({stock['stock_id']})")
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
            "institutional": args.institutional
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
                    print(f"📌 {concept['concept']} (熱度: {concept['heat_score']:.2f})")
                    print(f"   描述: {concept['description']}")
                    print(f"   趨勢: {concept['trend']}")
                    print(f"   股票數: {len(concept['stocks'])}")
                    print()
            else:
                print("❌ 沒有熱門概念股")
        else:
            print("❌ 無法取得熱門概念股")


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
                    print(f"  {i+1}. {rec['stock_name']} ({rec['stock_id']}) - 分數: {rec['composite_score']:.4f}")
            
            # 風險提示
            warnings = data.get("risk_warnings", [])
            if warnings:
                print(f"\n⚠️ 風險提示:")
                for warning in warnings:
                    print(f"  • {warning}")
        else:
            print("❌ AI 摘要生成失敗")


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
                "total_years": args.total_years
            }
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
                print(f"  • 風險調整後報酬: {overall.get('risk_adjusted_return', 'N/A')}")
                print(f"  • 正報酬期間: {overall.get('positive_periods', 0)}")
                print(f"  • 負報酬期間: {overall.get('negative_periods', 0)}")
        else:
            print("❌ Walk-Forward 驗證失敗")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="台灣股票分析工具 - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    stock_valuation_parser = stock_subparsers.add_parser("valuation", help="取得估值指標")
    stock_valuation_parser.add_argument("stock_id", help="股票代碼")
    
    # 多因子選股命令
    screener_parser = subparsers.add_parser("screener", help="多因子選股命令")
    screener_subparsers = screener_parser.add_subparsers(dest="screener_action")
    
    # screener run
    screener_run_parser = screener_subparsers.add_parser("run", help="執行選股篩選")
    screener_run_parser.add_argument("--top-n", type=int, default=10, help="返回前 N 名")
    
    # screener weights
    screener_weights_parser = screener_subparsers.add_parser("weights", help="更新因子權重")
    screener_weights_parser.add_argument("--momentum", type=float, default=0.2, help="動量因子權重")
    screener_weights_parser.add_argument("--value", type=float, default=0.25, help="價值因子權重")
    screener_weights_parser.add_argument("--quality", type=float, default=0.25, help="品質因子權重")
    screener_weights_parser.add_argument("--size", type=float, default=0.1, help="規模因子權重")
    screener_weights_parser.add_argument("--liquidity", type=float, default=0.1, help="流動性因子權重")
    screener_weights_parser.add_argument("--institutional", type=float, default=0.1, help="法人因子權重")
    
    # 產業分析命令
    industry_parser = subparsers.add_parser("industry", help="產業分析命令")
    industry_subparsers = industry_parser.add_subparsers(dest="industry_action")
    
    # industry ranking
    industry_ranking_parser = industry_subparsers.add_parser("ranking", help="產業強度排名")
    industry_ranking_parser.add_argument("--period", default="6mo", help="期間 (預設: 6mo)")
    
    # industry rotation
    industry_rotation_parser = industry_subparsers.add_parser("rotation", help="產業輪動分析")
    industry_rotation_parser.add_argument("--period", default="6mo", help="期間 (預設: 6mo)")
    
    # 概念股分析命令
    concept_parser = subparsers.add_parser("concept", help="概念股分析命令")
    concept_subparsers = concept_parser.add_subparsers(dest="concept_action")
    
    # concept ranking
    concept_ranking_parser = concept_subparsers.add_parser("ranking", help="概念股熱度排名")
    concept_ranking_parser.add_argument("--period", default="6mo", help="期間 (預設: 6mo)")
    
    # concept hot
    concept_hot_parser = concept_subparsers.add_parser("hot", help="熱門概念股")
    concept_hot_parser.add_argument("--period", default="6mo", help="期間 (預設: 6mo)")
    concept_hot_parser.add_argument("--min-heat", type=float, default=0.5, help="最低熱度分數")
    
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
    backtest_wf_parser = backtest_subparsers.add_parser("walk-forward", help="Walk-Forward 驗證")
    backtest_wf_parser.add_argument("stock_id", help="股票代碼")
    backtest_wf_parser.add_argument("strategy", help="策略名稱")
    backtest_wf_parser.add_argument("--train-window", type=int, default=252, help="訓練窗口")
    backtest_wf_parser.add_argument("--test-window", type=int, default=63, help="測試窗口")
    backtest_wf_parser.add_argument("--step-size", type=int, default=21, help="步進大小")
    backtest_wf_parser.add_argument("--total-years", type=int, default=5, help="總回測年數")
    
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
