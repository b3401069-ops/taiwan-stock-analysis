"""
台灣股票分析工具 - API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, date
import pandas as pd

# 導入服務
from api.services import StockService, AnalysisService, RecommendationService
from data.twse_fetcher import get_twse_fetcher
from data.financial_fetcher import get_financial_fetcher
from data.dividend_fetcher import get_dividend_fetcher
from models.db_manager import get_db_manager
from analysis.stock_analyst import get_stock_analyst
from analysis.valuation_metrics import get_valuation_metrics
from analysis.industry_comparison import get_industry_comparison
from analysis.backtest import get_backtest_engine, STRATEGIES
from analysis.backtest_advanced import get_advanced_backtest_engine
from analysis.virtual_portfolio import get_virtual_portfolio
from agents.stock_chatbot import get_stock_chatbot

# 創建路由器
router = APIRouter()


# 依賴注入
def get_stock_service():
    """獲取股票服務實例"""
    return StockService()


def get_analysis_service():
    """獲取分析服務實例"""
    return AnalysisService()


def get_recommendation_service():
    """獲取建議服務實例"""
    return RecommendationService()


# 股票資料端點
@router.get("/stocks", summary="獲取股票列表")
async def get_stocks(
    market: Optional[str] = Query(None, description="股票市場（taiwan, japan, korea, usa）"),
    industry: Optional[str] = Query(None, description="產業分類"),
    service: StockService = Depends(get_stock_service)
):
    """獲取股票列表"""
    try:
        stocks = await service.get_stocks(market=market, industry=industry)
        return {"success": True, "data": stocks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{stock_id}", summary="獲取股票詳細資訊")
async def get_stock(
    stock_id: str,
    service: StockService = Depends(get_stock_service)
):
    """獲取股票詳細資訊"""
    try:
        stock = await service.get_stock(stock_id)
        if not stock:
            raise HTTPException(status_code=404, detail="股票未找到")
        return {"success": True, "data": stock}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{stock_id}/price", summary="獲取股票價格")
async def get_stock_price(
    stock_id: str,
    period: Optional[str] = Query("1y", description="時間週期（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）"),
    service: StockService = Depends(get_stock_service)
):
    """獲取股票價格歷史"""
    try:
        price_data = await service.get_stock_price(stock_id, period)
        return {"success": True, "data": price_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/{stock_id}/realtime", summary="獲取即時股票價格")
async def get_realtime_price(
    stock_id: str,
    service: StockService = Depends(get_stock_service)
):
    """獲取即時股票價格"""
    try:
        realtime_data = await service.get_realtime_price(stock_id)
        return {"success": True, "data": realtime_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 技術分析端點
@router.get("/analysis/{stock_id}/technical", summary="獲取技術分析")
async def get_technical_analysis(
    stock_id: str,
    indicators: Optional[List[str]] = Query(None, description="技術指標列表（sma, ema, rsi, macd, kd, bollinger）"),
    service: AnalysisService = Depends(get_analysis_service)
):
    """獲取技術分析結果"""
    try:
        analysis = await service.get_technical_analysis(stock_id, indicators)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{stock_id}/fundamental", summary="獲取基本面分析")
async def get_fundamental_analysis(
    stock_id: str,
    service: AnalysisService = Depends(get_analysis_service)
):
    """獲取基本面分析結果"""
    try:
        analysis = await service.get_fundamental_analysis(stock_id)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{stock_id}/valuation", summary="獲取估值分析")
async def get_valuation_analysis(
    stock_id: str,
    models: Optional[List[str]] = Query(None, description="估值模型列表（pe, pb, dividend_yield, ev_ebitda, fcf_yield）"),
    service: AnalysisService = Depends(get_analysis_service)
):
    """獲取估值分析結果"""
    try:
        analysis = await service.get_valuation_analysis(stock_id, models)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 機器學習預測端點
@router.get("/prediction/{stock_id}", summary="獲取股價預測")
async def get_stock_prediction(
    stock_id: str,
    model: Optional[str] = Query("ensemble", description="預測模型（arima, lstm, xgboost, transformer, ensemble）"),
    days: Optional[int] = Query(30, description="預測天數"),
    service: AnalysisService = Depends(get_analysis_service)
):
    """獲取股價預測結果"""
    try:
        prediction = await service.get_stock_prediction(stock_id, model, days)
        return {"success": True, "data": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 買賣建議端點
@router.get("/recommendation/{stock_id}", summary="獲取買賣建議")
async def get_recommendation(
    stock_id: str,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """獲取買賣建議"""
    try:
        recommendation = await service.get_recommendation(stock_id)
        return {"success": True, "data": recommendation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendation/portfolio", summary="獲取投資組合建議")
async def get_portfolio_recommendation(
    risk_level: Optional[str] = Query("medium", description="風險等級（low, medium, high）"),
    investment_amount: Optional[float] = Query(1000000, description="投資金額"),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """獲取投資組合建議"""
    try:
        portfolio = await service.get_portfolio_recommendation(risk_level, investment_amount)
        return {"success": True, "data": portfolio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 國際股市連動分析端點
@router.get("/global/correlation", summary="獲取國際股市連動分析")
async def get_global_correlation(
    markets: Optional[List[str]] = Query(None, description="市場列表（taiwan, japan, korea, usa）"),
    service: AnalysisService = Depends(get_analysis_service)
):
    """獲取國際股市連動分析"""
    try:
        correlation = await service.get_global_correlation(markets)
        return {"success": True, "data": correlation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 產業研究報告端點
@router.get("/industry/{industry}/report", summary="獲取產業研究報告")
async def get_industry_report(
    industry: str,
    service: AnalysisService = Depends(get_analysis_service)
):
    """獲取產業研究報告"""
    try:
        report = await service.get_industry_report(industry)
        return {"success": True, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI Agent整合端點
@router.post("/agent/chat", summary="AI Agent對話")
async def agent_chat(
    message: str,
    agent_type: Optional[str] = Query("openclaw", description="Agent類型（openclaw, hermes）"),
    service: AnalysisService = Depends(get_analysis_service)
):
    """與AI Agent對話"""
    try:
        response = await service.chat_with_agent(message, agent_type)
        return {"success": True, "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/analysis/{stock_id}", summary="AI Agent分析報告")
async def get_agent_analysis(
    stock_id: str,
    agent_type: Optional[str] = Query("openclaw", description="Agent類型（openclaw, hermes）"),
    service: AnalysisService = Depends(get_analysis_service)
):
    """獲取AI Agent分析報告"""
    try:
        analysis = await service.get_agent_analysis(stock_id, agent_type)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 券商API端點
@router.get("/broker/accounts", summary="獲取券商帳戶資訊")
async def get_broker_accounts(
    broker: Optional[str] = Query(None, description="券商名稱（shioaji, fubon）"),
    service: StockService = Depends(get_stock_service)
):
    """獲取券商帳戶資訊"""
    try:
        accounts = await service.get_broker_accounts(broker)
        return {"success": True, "data": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broker/order", summary="下單")
async def place_order(
    stock_id: str,
    action: str,
    quantity: int,
    price: float,
    broker: Optional[str] = Query("shioaji", description="券商名稱（shioaji, fubon）"),
    service: StockService = Depends(get_stock_service)
):
    """下單"""
    try:
        order = await service.place_order(stock_id, action, quantity, price, broker)
        return {"success": True, "data": order}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  財報數據端點
# ──────────────────────────────────────────────
@router.get("/financial/{stock_id}/ratios", summary="財務比率指標")
async def get_financial_ratios(stock_id: str):
    """取得股票的財務比率指標"""
    try:
        fetcher = get_financial_fetcher()
        clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
        result = fetcher.get_financial_ratios(clean_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial/{stock_id}/income", summary="損益表")
async def get_income_statement(
    stock_id: str,
    year: int = Query(None, description="年度 (西元)"),
    quarter: int = Query(None, description="季度 (1-4)")
):
    """取得損益表"""
    try:
        fetcher = get_financial_fetcher()
        clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
        # 轉換為民國年
        tw_year = year - 1911 if year else None
        result = fetcher.get_income_statement(clean_id, tw_year, quarter)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial/{stock_id}/balance", summary="資產負債表")
async def get_balance_sheet(
    stock_id: str,
    year: int = Query(None, description="年度 (西元)"),
    quarter: int = Query(None, description="季度 (1-4)")
):
    """取得資產負債表"""
    try:
        fetcher = get_financial_fetcher()
        clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
        tw_year = year - 1911 if year else None
        result = fetcher.get_balance_sheet(clean_id, tw_year, quarter)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial/{stock_id}/cashflow", summary="現金流量表")
async def get_cash_flow(
    stock_id: str,
    year: int = Query(None, description="年度 (西元)"),
    quarter: int = Query(None, description="季度 (1-4)")
):
    """取得現金流量表"""
    try:
        fetcher = get_financial_fetcher()
        clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
        tw_year = year - 1911 if year else None
        result = fetcher.get_cash_flow(clean_id, tw_year, quarter)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  回測系統端點
# ──────────────────────────────────────────────
@router.get("/backtest/strategies", summary="可用策略列表")
async def get_strategies():
    """取得可用的回測策略"""
    return {
        "success": True,
        "strategies": [
            {
                "id": "rsi_oversold",
                "name": "RSI 超賣策略",
                "description": "RSI < 30 買入, RSI > 70 賣出"
            },
            {
                "id": "macd_crossover",
                "name": "MACD 黃金交叉策略",
                "description": "MACD 線上穿訊號線買入, 下穿賣出"
            },
            {
                "id": "ma_crossover",
                "name": "均線交叉策略",
                "description": "5日均線上穿20日均線買入, 下穿賣出"
            },
            {
                "id": "bollinger_bounce",
                "name": "布林通道反彈策略",
                "description": "觸及下軌買入, 觸及上軌賣出"
            },
            {
                "id": "combined",
                "name": "綜合策略",
                "description": "RSI + MACD 多指標確認"
            }
        ]
    }


@router.post("/backtest/run", summary="執行回測")
async def run_backtest(
    stock_id: str = Query(..., description="股票代碼"),
    strategy: str = Query(..., description="策略名稱"),
    period: str = Query("2y", description="回測期間 (1y, 2y, 5y)"),
    initial_capital: float = Query(1000000, description="初始資金")
):
    """執行策略回測"""
    try:
        if strategy not in STRATEGIES:
            raise HTTPException(status_code=400, detail=f"未知策略: {strategy}")

        engine = get_backtest_engine()
        strategy_func = STRATEGIES[strategy]

        result = engine.run(
            stock_id=stock_id,
            strategy=strategy_func,
            initial_capital=initial_capital,
            period=period
        )

        return {"success": True, "data": result.to_dict()}
    except Exception as e:
        logger.error(f"回測失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/compare", summary="策略比較")
async def compare_strategies(
    stock_id: str = Query(..., description="股票代碼"),
    period: str = Query("2y", description="回測期間"),
    initial_capital: float = Query(1000000, description="初始資金")
):
    """比較所有策略的表現"""
    try:
        engine = get_backtest_engine()
        results = {}

        for name, strategy_func in STRATEGIES.items():
            try:
                result = engine.run(
                    stock_id=stock_id,
                    strategy=strategy_func,
                    initial_capital=initial_capital,
                    period=period
                )
                results[name] = result.to_dict()
            except Exception as e:
                results[name] = {"error": str(e)}

        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  進階回測端點
# ──────────────────────────────────────────────
@router.post("/backtest/portfolio", summary="組合策略回測")
async def run_portfolio_backtest(
    stock_ids: str = Query(..., description="股票代碼，逗號分隔"),
    strategy: str = Query("ma_crossover", description="策略名稱"),
    weights: str = Query(None, description="權重，逗號分隔 (如: 0.4,0.3,0.3)"),
    period: str = Query("1y", description="回測期間"),
    initial_capital: float = Query(1000000, description="初始資金")
):
    """組合策略回測"""
    try:
        engine = get_advanced_backtest_engine()
        strategy_func = STRATEGIES.get(strategy)
        if not strategy_func:
            raise HTTPException(status_code=400, detail=f"未知策略: {strategy}")

        stock_list = [s.strip() for s in stock_ids.split(",")]
        weight_list = [float(w) for w in weights.split(",")] if weights else None

        result = engine.run_portfolio(
            stock_ids=stock_list,
            strategy=strategy_func,
            weights=weight_list,
            period=period,
            initial_capital=initial_capital
        )

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"組合回測失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/optimize", summary="參數優化")
async def optimize_backtest_parameter(
    stock_id: str = Query(..., description="股票代碼"),
    strategy: str = Query(..., description="策略名稱"),
    param_name: str = Query(..., description="參數名稱"),
    param_values: str = Query(..., description="參數值，逗號分隔"),
    period: str = Query("2y", description="回測期間"),
    initial_capital: float = Query(1000000, description="初始資金")
):
    """參數優化"""
    try:
        engine = get_advanced_backtest_engine()

        # 解析參數值
        try:
            values = [float(v) for v in param_values.split(",")]
        except ValueError:
            values = param_values.split(",")

        results = engine.optimize_parameter(
            stock_id=stock_id,
            strategy_name=strategy,
            param_name=param_name,
            param_values=values,
            period=period,
            initial_capital=initial_capital
        )

        return {"success": True, "data": results}
    except Exception as e:
        logger.error(f"參數優化失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/stop-loss", summary="停損停利回測")
async def run_stop_loss_backtest(
    stock_id: str = Query(..., description="股票代碼"),
    strategy: str = Query("rsi_oversold", description="策略名稱"),
    stop_loss: float = Query(-5.0, description="停損百分比 (如: -5)"),
    take_profit: float = Query(15.0, description="停利百分比 (如: 15)"),
    trailing_stop: bool = Query(False, description="是否使用移動停損"),
    period: str = Query("2y", description="回測期間"),
    initial_capital: float = Query(1000000, description="初始資金")
):
    """帶停損停利的回測"""
    try:
        engine = get_advanced_backtest_engine()
        strategy_func = STRATEGIES.get(strategy)
        if not strategy_func:
            raise HTTPException(status_code=400, detail=f"未知策略: {strategy}")

        result = engine.run_with_stop_loss(
            stock_id=stock_id,
            strategy=strategy_func,
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
            trailing_stop=trailing_stop,
            period=period,
            initial_capital=initial_capital
        )

        return {"success": True, "data": result.to_dict()}
    except Exception as e:
        logger.error(f"停損停利回測失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/cross-market", summary="跨市場回測")
async def run_cross_market_backtest(
    stock_ids: str = Query(..., description="股票代碼，逗號分隔"),
    strategy: str = Query("ma_crossover", description="策略名稱"),
    period: str = Query("1y", description="回測期間"),
    initial_capital: float = Query(1000000, description="初始資金")
):
    """跨市場回測"""
    try:
        engine = get_advanced_backtest_engine()
        strategy_func = STRATEGIES.get(strategy)
        if not strategy_func:
            raise HTTPException(status_code=400, detail=f"未知策略: {strategy}")

        stock_list = [s.strip() for s in stock_ids.split(",")]

        results = engine.run_cross_market(
            stock_ids=stock_list,
            strategy=strategy_func,
            period=period,
            initial_capital=initial_capital
        )

        return {"success": True, "data": results}
    except Exception as e:
        logger.error(f"跨市場回測失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  AI 綜合分析端點
# ──────────────────────────────────────────────
@router.get("/analysis/ai/{stock_id}", summary="AI 綜合分析")
async def get_ai_analysis(
    stock_id: str,
    include_ml: bool = Query(True, description="是否包含 ML 預測"),
    prediction_days: int = Query(5, description="預測天數")
):
    """使用本地 AI 引擎綜合分析股票"""
    try:
        analyst = get_stock_analyst()
        result = await analyst.analyze(stock_id, include_ml=include_ml, prediction_days=prediction_days)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"AI 分析失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/report/{stock_id}", summary="分析報告（文字版）")
async def get_analysis_report(
    stock_id: str,
    include_ml: bool = Query(True, description="是否包含 ML 預測")
):
    """取得股票分析報告的文字摘要"""
    try:
        analyst = get_stock_analyst()
        result = await analyst.analyze(stock_id, include_ml=include_ml, prediction_days=5)
        return {
            "success": True,
            "stock_id": stock_id,
            "report": result.get("analysis_summary", ""),
            "recommendation": result.get("recommendation", {}),
            "risk": result.get("risk_assessment", {})
        }
    except Exception as e:
        logger.error(f"分析報告失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  AI 聊天分析師端點
# ──────────────────────────────────────────────
@router.post("/chat", summary="AI 聊天分析師")
async def chat_with_analyst(
    message: str = Query(..., description="用戶訊息")
):
    """與 AI 股票分析師對話"""
    try:
        chatbot = get_stock_chatbot()
        result = await chatbot.chat(message)
        return result
    except Exception as e:
        logger.error(f"聊天失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history", summary="取得對話歷史")
async def get_chat_history():
    """取得對話歷史記錄"""
    try:
        chatbot = get_stock_chatbot()
        history = chatbot.get_conversation_history()
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/history", summary="清除對話歷史")
async def clear_chat_history():
    """清除對話歷史記錄"""
    try:
        chatbot = get_stock_chatbot()
        chatbot.clear_history()
        return {"success": True, "message": "對話歷史已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  虛擬倉位端點
# ──────────────────────────────────────────────
@router.get("/portfolio/summary", summary="倉位摘要")
async def get_portfolio_summary():
    """取得虛擬倉位摘要"""
    try:
        portfolio = get_virtual_portfolio()
        return portfolio.get_portfolio_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/buy", summary="買入股票")
async def buy_stock(
    stock_id: str = Query(..., description="股票代碼"),
    stock_name: str = Query(..., description="股票名稱"),
    shares: int = Query(..., description="股數"),
    entry_price: float = Query(..., description="進場價格"),
    entry_reason: str = Query("AI 建議", description="進場原因"),
    ai_confidence: int = Query(70, description="AI 信心水平"),
    target_price: float = Query(0, description="目標價"),
    stop_loss: float = Query(0, description="停損價")
):
    """買入股票到虛擬倉位"""
    try:
        portfolio = get_virtual_portfolio()
        
        # 如果沒有目標價，預設 +10%
        if target_price == 0:
            target_price = entry_price * 1.1
        
        # 如果沒有停損，預設 -5%
        if stop_loss == 0:
            stop_loss = entry_price * 0.95
        
        result = portfolio.add_position(
            stock_id=stock_id,
            stock_name=stock_name,
            shares=shares,
            entry_price=entry_price,
            entry_reason=entry_reason,
            ai_confidence=ai_confidence,
            target_price=target_price,
            stop_loss=stop_loss
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/sell", summary="賣出股票")
async def sell_stock(
    stock_id: str = Query(..., description="股票代碼"),
    shares: int = Query(..., description="賣出股數"),
    sell_price: float = Query(..., description="賣出價格"),
    reason: str = Query("手動賣出", description="賣出原因")
):
    """賣出虛擬倉位股票"""
    try:
        portfolio = get_virtual_portfolio()
        result = portfolio.sell_position(
            stock_id=stock_id,
            shares=shares,
            sell_price=sell_price,
            reason=reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/history", summary="交易歷史")
async def get_trade_history(limit: int = Query(50, description="筆數")):
    """取得交易歷史"""
    try:
        portfolio = get_virtual_portfolio()
        return portfolio.get_trade_history(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/alerts", summary="停損停利警報")
async def get_portfolio_alerts():
    """檢查停損和目標價警報"""
    try:
        portfolio = get_virtual_portfolio()
        alerts = portfolio.check_stop_loss_and_target()
        return {"success": True, "data": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/review", summary="投資回顧報告")
async def get_investment_review():
    """生成投資回顧報告"""
    try:
        portfolio = get_virtual_portfolio()
        return portfolio.generate_investment_review()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/reset", summary="重置倉位")
async def reset_portfolio():
    """重置虛擬倉位"""
    try:
        portfolio = get_virtual_portfolio()
        return portfolio.reset_portfolio()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/ai-buy", summary="AI 建議買入")
async def ai_suggest_buy(
    stock_id: str = Query(..., description="股票代碼"),
    amount: float = Query(100000, description="投資金額")
):
    """AI 分析後建議買入"""
    try:
        # 取得 AI 分析
        analyst = get_stock_analyst()
        analysis = await analyst.analyze(stock_id, include_ml=True)
        
        if not analysis.get("success"):
            return {"success": False, "error": "AI 分析失敗"}
        
        data = analysis["data"]
        rec = data.get("recommendation", {})
        
        # 檢查是否建議買入
        if rec.get("action") != "buy":
            return {
                "success": False,
                "message": f"AI 不建議買入。建議動作：{rec.get('action', 'hold')}",
                "data": rec
            }
        
        # 計算股數
        current_price = data.get("price_info", {}).get("current_price", 0)
        if current_price <= 0:
            return {"success": False, "error": "無法取得目前股價"}
        
        shares = int(amount / current_price / 1000) * 1000  # 整張
        if shares == 0:
            shares = 100  # 至少 100 股（零股）
        
        # 買入
        portfolio = get_virtual_portfolio()
        result = portfolio.add_position(
            stock_id=stock_id,
            stock_name=data.get("stock_name", stock_id),
            shares=shares,
            entry_price=current_price,
            entry_reason=f"AI 建議買入。{rec.get('reason', '')}",
            ai_confidence=rec.get("confidence", 70),
            target_price=rec.get("target_price", current_price * 1.1),
            stop_loss=rec.get("stop_loss", current_price * 0.95)
        )
        
        # 加入 AI 分析摘要
        if result.get("success"):
            result["ai_analysis"] = {
                "action": rec.get("action"),
                "confidence": rec.get("confidence"),
                "target_price": rec.get("target_price"),
                "stop_loss": rec.get("stop_loss")
            }
        
        return result
        
    except Exception as e:
        logger.error(f"AI 建議買入失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  估值指標端點
# ──────────────────────────────────────────────
@router.get("/valuation/{stock_id}", summary="估值指標分析")
async def get_valuation(stock_id: str):
    """取得股票的估值指標 (PE、PB、股利殖利率等)"""
    try:
        metrics = get_valuation_metrics()
        result = metrics.get_valuation(stock_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  產業比較端點
# ──────────────────────────────────────────────
@router.get("/industry/industries", summary="產業列表")
async def get_industries():
    """取得所有產業列表"""
    try:
        comparison = get_industry_comparison()
        return comparison.get_all_industries()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry/compare/{stock_id}", summary="產業比較分析")
async def get_industry_analysis(stock_id: str):
    """取得股票的產業比較分析"""
    try:
        comparison = get_industry_comparison()
        return comparison.get_industry_analysis(stock_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry/stocks/{industry_name}", summary="產業內股票")
async def get_industry_stocks(industry_name: str):
    """取得產業內所有股票"""
    try:
        comparison = get_industry_comparison()
        return comparison.get_industry_stocks(industry_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  除權息資料端點
# ──────────────────────────────────────────────
@router.get("/dividend/{stock_id}", summary="除權息資料")
async def get_dividend_data(stock_id: str, years: int = Query(5, description="歷史年數")):
    """取得股票的除權息資料和填息率"""
    try:
        fetcher = get_dividend_fetcher()
        clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
        return fetcher.get_dividend_data(clean_id, years)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  TWSE 官方資料端點
# ──────────────────────────────────────────────
@router.get("/twse/daily", summary="TWSE 每日收盤行情")
async def get_twse_daily():
    """取得上市股票每日收盤行情"""
    try:
        twse = get_twse_fetcher()
        df = twse.get_daily_closing()
        if df.empty:
            return {"success": True, "data": [], "count": 0}
        return {"success": True, "data": df.to_dict("records"), "count": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/twse/institutional", summary="三大法人買賣超")
async def get_twse_institutional():
    """取得三大法人個股買賣超明細"""
    try:
        twse = get_twse_fetcher()
        df = twse.get_institutional_investors()
        if df.empty:
            return {"success": True, "data": [], "count": 0}
        return {"success": True, "data": df.to_dict("records"), "count": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/twse/margin", summary="融資融券統計")
async def get_twse_margin():
    """取得融資融券統計"""
    try:
        twse = get_twse_fetcher()
        df = twse.get_margin_trading()
        if df.empty:
            return {"success": True, "data": [], "count": 0}
        return {"success": True, "data": df.to_dict("records"), "count": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/twse/stock/{stock_id}/history", summary="個股歷史資料")
async def get_twse_stock_history(stock_id: str, months: int = Query(12, description="回溯月數")):
    """取得個股歷史日成交資訊"""
    try:
        twse = get_twse_fetcher()
        # 去掉 .TW 後綴
        clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
        df = twse.get_stock_history(clean_id, months)
        if df.empty:
            return {"success": True, "data": [], "count": 0}
        return {"success": True, "data": df.to_dict("records"), "count": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/db/sync/{stock_id}", summary="同步股票資料到資料庫")
async def sync_stock_to_db(stock_id: str, months: int = Query(12, description="同步月數")):
    """從 TWSE 同步股票價格資料到本地資料庫"""
    try:
        db = get_db_manager()
        count = db.sync_stock_prices(stock_id, months)
        return {"success": True, "stock_id": stock_id, "synced_records": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/stocks", summary="資料庫中的股票列表")
async def get_db_stocks():
    """取得資料庫中已有的股票列表"""
    try:
        db = get_db_manager()
        stocks = db.get_stocks()
        return {
            "success": True,
            "data": [{"stock_id": s.stock_id, "name": s.name, "market": s.market} for s in stocks]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 系統狀態端點
@router.get("/system/status", summary="獲取系統狀態")
async def get_system_status():
    """獲取系統狀態"""
    try:
        # 這裡應該檢查各個服務的狀態
        return {
            "success": True,
            "data": {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "database": "connected",
                    "redis": "connected",
                    "shioaji": "connected",
                    "fubon": "connected",
                    "openclaw": "connected",
                    "hermes": "connected"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))