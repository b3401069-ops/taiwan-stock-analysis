"""
台灣股票分析工具 - 功能演示腳本
"""

import json
import time
from datetime import datetime
from typing import Any, Dict

import requests

# API基礎URL
BASE_URL = "http://localhost:8000/api/v1"


class StockAnalysisDemo:
    """股票分析演示類"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def check_health(self) -> bool:
        """檢查服務健康狀態"""
        try:
            response = self.session.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服務狀態: {data.get('status', 'unknown')}")
                print(f"   應用: {data.get('app', 'unknown')}")
                print(f"   版本: {data.get('version', 'unknown')}")
                return True
            else:
                print(f"❌ 服務異常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 無法連接到服務: {e}")
            return False

    def get_stock_list(self, market: str = "taiwan") -> Dict:
        """獲取股票列表"""
        try:
            response = self.session.get(f"{BASE_URL}/stocks", params={"market": market})

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stocks = data.get("data", [])
                    print(f"✅ 獲取股票列表成功")
                    print(f"   市場: {market}")
                    print(f"   股票數量: {len(stocks)}")

                    # 顯示前5個股票
                    for i, stock in enumerate(stocks[:5]):
                        print(f"   {i+1}. {stock.get('id')} - {stock.get('name')}")

                    return data

            print(f"❌ 獲取股票列表失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取股票列表異常: {e}")
            return {}

    def get_stock_price(self, stock_id: str, period: str = "1mo") -> Dict:
        """獲取股票價格"""
        try:
            response = self.session.get(
                f"{BASE_URL}/stocks/{stock_id}/price", params={"period": period}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    price_data = data.get("data", {})
                    summary = price_data.get("summary", {})

                    print(f"✅ 獲取股票價格成功")
                    print(f"   股票代碼: {stock_id}")
                    print(f"   時間週期: {period}")
                    print(f"   最新價格: {summary.get('latest_price', 'N/A')}")
                    print(f"   最高價格: {summary.get('highest_price', 'N/A')}")
                    print(f"   最低價格: {summary.get('lowest_price', 'N/A')}")
                    print(f"   平均價格: {summary.get('average_price', 'N/A')}")

                    return data

            print(f"❌ 獲取股票價格失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取股票價格異常: {e}")
            return {}

    def get_realtime_price(self, stock_id: str) -> Dict:
        """獲取即時股票價格"""
        try:
            response = self.session.get(f"{BASE_URL}/stocks/{stock_id}/realtime")

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    realtime_data = data.get("data", {})

                    print(f"✅ 獲取即時股票價格成功")
                    print(f"   股票代碼: {stock_id}")
                    print(f"   當前價格: {realtime_data.get('price', 'N/A')}")
                    print(f"   漲跌: {realtime_data.get('change', 'N/A')}")
                    print(f"   漲跌幅: {realtime_data.get('change_percent', 'N/A')}%")
                    print(f"   成交量: {realtime_data.get('volume', 'N/A')}")
                    print(f"   本益比: {realtime_data.get('pe_ratio', 'N/A')}")
                    print(
                        f"   股利殖利率: {realtime_data.get('dividend_yield', 'N/A')}"
                    )

                    return data

            print(f"❌ 獲取即時股票價格失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取即時股票價格異常: {e}")
            return {}

    def get_technical_analysis(self, stock_id: str, indicators: list = None) -> Dict:
        """獲取技術分析"""
        try:
            params = {}
            if indicators:
                params["indicators"] = ",".join(indicators)

            response = self.session.get(
                f"{BASE_URL}/analysis/{stock_id}/technical", params=params
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    analysis = data.get("data", {})
                    signals = analysis.get("signals", {})

                    print(f"✅ 獲取技術分析成功")
                    print(f"   股票代碼: {stock_id}")
                    print(f"   總體信號: {signals.get('overall_signal', 'N/A')}")
                    print(f"   信心水平: {signals.get('confidence', 'N/A')}")

                    # 顯示買入信號
                    buy_signals = signals.get("buy_signals", [])
                    if buy_signals:
                        print(f"   買入信號:")
                        for signal in buy_signals:
                            print(
                                f"     - {signal.get('indicator')}: {signal.get('reason')}"
                            )

                    # 顯示賣出信號
                    sell_signals = signals.get("sell_signals", [])
                    if sell_signals:
                        print(f"   賣出信號:")
                        for signal in sell_signals:
                            print(
                                f"     - {signal.get('indicator')}: {signal.get('reason')}"
                            )

                    return data

            print(f"❌ 獲取技術分析失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取技術分析異常: {e}")
            return {}

    def get_fundamental_analysis(self, stock_id: str) -> Dict:
        """獲取基本面分析"""
        try:
            response = self.session.get(f"{BASE_URL}/analysis/{stock_id}/fundamental")

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    analysis = data.get("data", {})
                    summary = analysis.get("summary", {})

                    print(f"✅ 獲取基本面分析成功")
                    print(f"   股票代碼: {stock_id}")
                    print(f"   總體評級: {summary.get('overall_rating', 'N/A')}")
                    print(f"   投資建議: {summary.get('recommendation', 'N/A')}")

                    # 顯示優勢
                    strengths = summary.get("strengths", [])
                    if strengths:
                        print(f"   優勢:")
                        for strength in strengths:
                            print(f"     - {strength}")

                    # 顯示劣勢
                    weaknesses = summary.get("weaknesses", [])
                    if weaknesses:
                        print(f"   劣勢:")
                        for weakness in weaknesses:
                            print(f"     - {weakness}")

                    return data

            print(f"❌ 獲取基本面分析失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取基本面分析異常: {e}")
            return {}

    def get_valuation_analysis(self, stock_id: str, models: list = None) -> Dict:
        """獲取估值分析"""
        try:
            params = {}
            if models:
                params["models"] = ",".join(models)

            response = self.session.get(
                f"{BASE_URL}/analysis/{stock_id}/valuation", params=params
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    analysis = data.get("data", {})
                    summary = analysis.get("summary", {})

                    print(f"✅ 獲取估值分析成功")
                    print(f"   股票代碼: {stock_id}")
                    print(f"   總體估值: {summary.get('overall_valuation', 'N/A')}")
                    print(f"   投資建議: {summary.get('recommendation', 'N/A')}")
                    print(f"   上漲潛力: {summary.get('upside_potential', 'N/A')}")

                    # 顯示低估模型
                    undervalued_models = summary.get("undervalued_models", [])
                    if undervalued_models:
                        print(f"   低估模型: {', '.join(undervalued_models)}")

                    # 顯示高估模型
                    overvalued_models = summary.get("overvalued_models", [])
                    if overvalued_models:
                        print(f"   高估模型: {', '.join(overvalued_models)}")

                    return data

            print(f"❌ 獲取估值分析失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取估值分析異常: {e}")
            return {}

    def get_stock_prediction(
        self, stock_id: str, model: str = "ensemble", days: int = 30
    ) -> Dict:
        """獲取股價預測"""
        try:
            response = self.session.get(
                f"{BASE_URL}/prediction/{stock_id}",
                params={"model": model, "days": days},
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    prediction = data.get("data", {})
                    summary = prediction.get("summary", {})

                    print(f"✅ 獲取股價預測成功")
                    print(f"   股票代碼: {stock_id}")
                    print(f"   預測模型: {model}")
                    print(f"   預測天數: {days}")
                    print(f"   趨勢: {summary.get('trend', 'N/A')}")
                    print(f"   信心水平: {summary.get('confidence', 'N/A')}")
                    print(f"   預期收益率: {summary.get('expected_return', 'N/A')}")
                    print(f"   投資建議: {summary.get('recommendation', 'N/A')}")

                    return data

            print(f"❌ 獲取股價預測失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取股價預測異常: {e}")
            return {}

    def get_recommendation(self, stock_id: str) -> Dict:
        """獲取買賣建議"""
        try:
            response = self.session.get(f"{BASE_URL}/recommendation/{stock_id}")

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    recommendation = data.get("data", {})
                    overall = recommendation.get("overall_recommendation", {})
                    risk = recommendation.get("risk_assessment", {})
                    action = recommendation.get("action_plan", {})

                    print(f"✅ 獲取買賣建議成功")
                    print(f"   股票代碼: {stock_id}")
                    print(f"   投資建議: {overall.get('recommendation', 'N/A')}")
                    print(f"   信心水平: {overall.get('confidence', 'N/A')}")
                    print(f"   加權分數: {overall.get('weighted_score', 'N/A')}")

                    # 顯示理由
                    reasoning = overall.get("reasoning", [])
                    if reasoning:
                        print(f"   建議理由:")
                        for reason in reasoning:
                            print(f"     - {reason}")

                    # 顯示風險評估
                    print(f"   風險等級: {risk.get('risk_level', 'N/A')}")

                    # 顯示行動計劃
                    print(f"   立即行動: {action.get('immediate_action', 'N/A')}")

                    return data

            print(f"❌ 獲取買賣建議失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取買賣建議異常: {e}")
            return {}

    def get_portfolio_recommendation(
        self, risk_level: str = "medium", investment_amount: float = 1000000
    ) -> Dict:
        """獲取投資組合建議"""
        try:
            response = self.session.get(
                f"{BASE_URL}/recommendation/portfolio",
                params={
                    "risk_level": risk_level,
                    "investment_amount": investment_amount,
                },
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    portfolio = data.get("data", {})
                    allocation = portfolio.get("allocation", {})
                    metrics = portfolio.get("expected_metrics", {})

                    print(f"✅ 獲取投資組合建議成功")
                    print(f"   風險等級: {risk_level}")
                    print(f"   投資金額: NT${investment_amount:,.0f}")
                    print(f"   預期收益率: {metrics.get('expected_return', 'N/A')}")
                    print(f"   預期波動率: {metrics.get('expected_volatility', 'N/A')}")
                    print(f"   夏普比率: {metrics.get('sharpe_ratio', 'N/A')}")

                    # 顯示股票配置
                    stocks = allocation.get("stocks", [])
                    if stocks:
                        print(f"   股票配置:")
                        for stock in stocks:
                            print(
                                f"     - {stock.get('name')} ({stock.get('stock_id')}): {stock.get('weight')*100:.1f}%"
                            )

                    return data

            print(f"❌ 獲取投資組合建議失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取投資組合建議異常: {e}")
            return {}

    def chat_with_agent(self, message: str, agent_type: str = "openclaw") -> Dict:
        """與AI Agent對話"""
        try:
            response = self.session.post(
                f"{BASE_URL}/agent/chat",
                params={"message": message, "agent_type": agent_type},
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    agent_response = data.get("data", {})

                    print(f"✅ AI Agent對話成功")
                    print(f"   Agent類型: {agent_type}")
                    print(f"   使用模型: {agent_response.get('model', 'N/A')}")
                    print(f"   回應內容:")
                    print(f"   {agent_response.get('response', 'N/A')}")

                    return data

            print(f"❌ AI Agent對話失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ AI Agent對話異常: {e}")
            return {}

    def get_global_correlation(self, markets: list = None) -> Dict:
        """獲取國際股市連動分析"""
        try:
            params = {}
            if markets:
                params["markets"] = ",".join(markets)

            response = self.session.get(f"{BASE_URL}/global/correlation", params=params)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    correlation = data.get("data", {})

                    print(f"✅ 獲取國際股市連動分析成功")
                    print(f"   市場: {', '.join(markets) if markets else 'all'}")

                    return data

            print(f"❌ 獲取國際股市連動分析失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取國際股市連動分析異常: {e}")
            return {}

    def get_broker_accounts(self, broker: str = None) -> Dict:
        """獲取券商帳戶資訊"""
        try:
            params = {}
            if broker:
                params["broker"] = broker

            response = self.session.get(f"{BASE_URL}/broker/accounts", params=params)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    accounts = data.get("data", [])

                    print(f"✅ 獲取券商帳戶資訊成功")
                    for account in accounts:
                        print(f"   券商: {account.get('broker')}")
                        print(f"   帳戶: {account.get('account')}")
                        print(f"   餘額: NT${account.get('balance', 0):,.0f}")

                    return data

            print(f"❌ 獲取券商帳戶資訊失敗: {response.status_code}")
            return {}

        except Exception as e:
            print(f"❌ 獲取券商帳戶資訊異常: {e}")
            return {}

    def run_full_analysis(self, stock_id: str) -> Dict:
        """執行完整分析"""
        print(f"\n{'='*60}")
        print(f"股票完整分析報告 - {stock_id}")
        print(f"{'='*60}")

        results = {}

        # 1. 獲取即時價格
        print(f"\n1. 獲取即時價格...")
        results["realtime"] = self.get_realtime_price(stock_id)

        # 2. 獲取技術分析
        print(f"\n2. 獲取技術分析...")
        results["technical"] = self.get_technical_analysis(stock_id)

        # 3. 獲取基本面分析
        print(f"\n3. 獲取基本面分析...")
        results["fundamental"] = self.get_fundamental_analysis(stock_id)

        # 4. 獲取估值分析
        print(f"\n4. 獲取估值分析...")
        results["valuation"] = self.get_valuation_analysis(stock_id)

        # 5. 獲取股價預測
        print(f"\n5. 獲取股價預測...")
        results["prediction"] = self.get_stock_prediction(stock_id)

        # 6. 獲取買賣建議
        print(f"\n6. 獲取買賣建議...")
        results["recommendation"] = self.get_recommendation(stock_id)

        # 7. AI Agent分析
        print(f"\n7. AI Agent分析...")
        results["ai_analysis"] = self.chat_with_agent(
            f"請分析{stock_id}的投資價值", "openclaw"
        )

        print(f"\n{'='*60}")
        print(f"分析完成！")
        print(f"{'='*60}")

        return results


def main():
    """主函數"""
    demo = StockAnalysisDemo()

    print("台灣股票分析工具 - 功能演示")
    print("=" * 60)

    # 檢查服務健康狀態
    if not demo.check_health():
        print("\n請先啟動服務：python main.py")
        return

    # 演示各項功能
    print("\n" + "=" * 60)
    print("功能演示開始")
    print("=" * 60)

    # 1. 獲取股票列表
    print("\n1. 獲取股票列表")
    demo.get_stock_list("taiwan")

    # 2. 獲取台積電即時價格
    print("\n2. 獲取台積電即時價格")
    demo.get_realtime_price("2330.TW")

    # 3. 獲取技術分析
    print("\n3. 獲取技術分析")
    demo.get_technical_analysis("2330.TW", ["rsi", "macd", "kd"])

    # 4. 獲取基本面分析
    print("\n4. 獲取基本面分析")
    demo.get_fundamental_analysis("2330.TW")

    # 5. 獲取估值分析
    print("\n5. 獲取估值分析")
    demo.get_valuation_analysis("2330.TW", ["pe", "pb", "dividend_yield"])

    # 6. 獲取股價預測
    print("\n6. 獲取股價預測")
    demo.get_stock_prediction("2330.TW", "ensemble", 30)

    # 7. 獲取買賣建議
    print("\n7. 獲取買賣建議")
    demo.get_recommendation("2330.TW")

    # 8. 獲取投資組合建議
    print("\n8. 獲取投資組合建議")
    demo.get_portfolio_recommendation("medium", 1000000)

    # 9. AI Agent對話
    print("\n9. AI Agent對話")
    demo.chat_with_agent("請分析台積電的投資價值", "openclaw")

    # 10. 獲取國際股市連動分析
    print("\n10. 獲取國際股市連動分析")
    demo.get_global_correlation(["taiwan", "japan", "korea", "usa"])

    print("\n" + "=" * 60)
    print("功能演示完成！")
    print("=" * 60)

    # 詢問是否執行完整分析
    print("\n是否執行台積電(2330.TW)的完整分析？(y/n)")
    choice = input().strip().lower()

    if choice == "y":
        demo.run_full_analysis("2330.TW")


if __name__ == "__main__":
    main()
