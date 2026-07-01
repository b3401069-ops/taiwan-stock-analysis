"""
台灣股票分析工具 - Streamlit 儀表板
提供專業的前端儀表板，整合所有分析功能
參考 taiwan-quant-project 的 visualization/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import time

# 設定頁面配置
st.set_page_config(
    page_title="台灣股票分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 基礎 URL
API_BASE = "http://localhost:9999/api/v1"

# 自定義 CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .positive { color: #28a745; }
    .negative { color: #dc3545; }
    .neutral { color: #6c757d; }
</style>
""", unsafe_allow_html=True)


def call_api(endpoint, method="GET", params=None, data=None):
    """調用 API"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, params=params, json=data, timeout=30)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 錯誤: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"API 連接失敗: {e}")
        return None


def create_stock_chart(df, title="股票價格走勢"):
    """建立股票價格圖表"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(title, '成交量'),
        row_width=[0.7, 0.3]
    )
    
    # 添加K線圖
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K線'
        ),
        row=1, col=1
    )
    
    # 添加移動平均線
    if 'ma5' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['ma5'], name='MA5', line=dict(color='orange', width=1)),
            row=1, col=1
        )
    if 'ma20' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['ma20'], name='MA20', line=dict(color='blue', width=1)),
            row=1, col=1
        )
    
    # 添加成交量
    colors = ['green' if close >= open else 'red' for close, open in zip(df['close'], df['open'])]
    fig.add_trace(
        go.Bar(x=df.index, y=df['volume'], name='成交量', marker_color=colors),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        template="plotly_white"
    )
    
    return fig


def market_overview_page():
    """市場總覽頁面"""
    st.markdown('<div class="main-header"><h1>📊 台灣股票分析工具 - 市場總覽</h1></div>', unsafe_allow_html=True)
    
    # 市場狀態
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("加權指數", "17,234.56", "+123.45")
    
    with col2:
        st.metric("成交量", "2,345億", "+12%")
    
    with col3:
        st.metric("上漲家數", "456", "+23")
    
    with col4:
        st.metric("下跌家數", "234", "-12")
    
    # 市場狀態分析
    st.subheader("📈 市場狀態分析")
    
    market_data = call_api("/market/regime")
    if market_data and market_data.get("success"):
        regime_data = market_data["data"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**市場狀態**: {regime_data.get('regime_name', 'N/A')}")
            st.write(f"**信心水平**: {regime_data.get('confidence', 0)}%")
            st.write(f"**建議動作**: {regime_data.get('suggestion', {}).get('action', 'N/A')}")
        
        with col2:
            st.write(f"**分析原因**: {regime_data.get('suggestion', {}).get('reason', 'N/A')}")
    
    # 產業輪動分析
    st.subheader("🏭 產業輪動分析")
    
    industry_data = call_api("/industry/ranking?period=3mo")
    if industry_data and industry_data.get("success"):
        industry_df = pd.DataFrame(industry_data["data"])
        
        fig = px.bar(
            industry_df,
            x='industry',
            y='strength_score',
            color='signal',
            title='產業強度排名',
            labels={'strength_score': '強度分數', 'industry': '產業'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 概念股輪動分析
    st.subheader("💡 概念股輪動分析")
    
    concept_data = call_api("/concept/ranking?period=3mo")
    if concept_data and concept_data.get("success"):
        concept_df = pd.DataFrame(concept_data["data"])
        
        fig = px.bar(
            concept_df,
            x='concept',
            y='heat_score',
            color='trend',
            title='概念股熱度排名',
            labels={'heat_score': '熱度分數', 'concept': '概念股'}
        )
        st.plotly_chart(fig, use_container_width=True)


def stock_analysis_page():
    """個股分析頁面"""
    st.markdown('<div class="main-header"><h1>📈 個股分析</h1></div>', unsafe_allow_html=True)
    
    # 股票輸入
    stock_id = st.text_input("輸入股票代碼", "2330.TW")
    period = st.selectbox("選擇時間範圍", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
    
    if st.button("開始分析"):
        with st.spinner("正在分析..."):
            # 取得股票資料
            stock_data = call_api(f"/stock/{stock_id}")
            price_data = call_api(f"/price/{stock_id}?period={period}")
            valuation_data = call_api(f"/valuation/{stock_id}")
            
            if stock_data and stock_data.get("success"):
                # 顯示基本資訊
                st.subheader(f"📊 {stock_id} 基本資訊")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("股票代碼", stock_id)
                
                with col2:
                    st.metric("股票名稱", stock_data["data"].get("name", "N/A"))
                
                with col3:
                    st.metric("市場", stock_data["data"].get("market", "N/A"))
                
                with col4:
                    st.metric("產業", stock_data["data"].get("industry", "N/A"))
            
            # 顯示價格圖表
            if price_data and price_data.get("success"):
                st.subheader(f"📈 {stock_id} 價格走勢")
                
                # 準備資料
                price_df = pd.DataFrame(price_data["data"])
                price_df['date'] = pd.to_datetime(price_df['date'])
                price_df.set_index('date', inplace=True)
                
                # 計算移動平均線
                price_df['ma5'] = price_df['close'].rolling(window=5).mean()
                price_df['ma20'] = price_df['close'].rolling(window=20).mean()
                
                # 建立圖表
                fig = create_stock_chart(price_df, f"{stock_id} 價格走勢")
                st.plotly_chart(fig, use_container_width=True)
            
            # 顯示估值指標
            if valuation_data and valuation_data.get("success"):
                st.subheader(f"💰 {stock_id} 估值指標")
                
                valuation = valuation_data["data"]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("本益比 (PE)", f"{valuation.get('pe_ratio', 0):.2f}")
                
                with col2:
                    st.metric("股價淨值比 (PB)", f"{valuation.get('pb_ratio', 0):.2f}")
                
                with col3:
                    st.metric("股利殖利率", f"{valuation.get('dividend_yield', 0):.2f}%")
                
                with col4:
                    st.metric("估值評級", valuation.get('valuation_rating', 'N/A'))


def screener_page():
    """多因子選股頁面"""
    st.markdown('<div class="main-header"><h1>🔍 多因子選股</h1></div>', unsafe_allow_html=True)
    
    # 因子權重設定
    st.subheader("⚖️ 因子權重設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        momentum_weight = st.slider("動量因子", 0.0, 1.0, 0.2, 0.05)
        value_weight = st.slider("價值因子", 0.0, 1.0, 0.25, 0.05)
        quality_weight = st.slider("品質因子", 0.0, 1.0, 0.25, 0.05)
    
    with col2:
        size_weight = st.slider("規模因子", 0.0, 1.0, 0.1, 0.05)
        liquidity_weight = st.slider("流動性因子", 0.0, 1.0, 0.1, 0.05)
        institutional_weight = st.slider("法人因子", 0.0, 1.0, 0.1, 0.05)
    
    # 更新權重
    if st.button("更新因子權重"):
        weights = {
            "momentum": momentum_weight,
            "value": value_weight,
            "quality": quality_weight,
            "size": size_weight,
            "liquidity": liquidity_weight,
            "institutional": institutional_weight
        }
        
        result = call_api("/screener/weights", method="POST", data=weights)
        if result and result.get("success"):
            st.success("因子權重更新成功！")
    
    # 選股篩選
    st.subheader("📊 選股篩選")
    
    top_n = st.number_input("返回前 N 名", min_value=1, max_value=50, value=10)
    
    if st.button("開始篩選"):
        with st.spinner("正在篩選..."):
            result = call_api("/screener/multi-factor", method="POST", params={"top_n": top_n})
            
            if result and result.get("success"):
                stocks = result["data"]
                
                if stocks:
                    # 建立資料表
                    stock_df = pd.DataFrame(stocks)
                    
                    # 顯示圖表
                    fig = px.bar(
                        stock_df,
                        x='stock_name',
                        y='composite_score',
                        title='多因子選股結果',
                        labels={'composite_score': '綜合分數', 'stock_name': '股票名稱'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 顯示詳細資料
                    st.dataframe(stock_df[['rank', 'stock_id', 'stock_name', 'composite_score']])
                else:
                    st.warning("沒有篩選結果")


def industry_rotation_page():
    """產業輪動分析頁面"""
    st.markdown('<div class="main-header"><h1>🏭 產業輪動分析</h1></div>', unsafe_allow_html=True)
    
    period = st.selectbox("選擇分析期間", ["3mo", "6mo", "1y"], index=1)
    
    if st.button("開始分析"):
        with st.spinner("正在分析..."):
            # 產業排名
            ranking_data = call_api(f"/industry/ranking?period={period}")
            
            if ranking_data and ranking_data.get("success"):
                st.subheader("📊 產業強度排名")
                
                ranking_df = pd.DataFrame(ranking_data["data"])
                
                # 建立圖表
                fig = px.bar(
                    ranking_df,
                    x='industry',
                    y='strength_score',
                    color='signal',
                    title='產業強度排名',
                    labels={'strength_score': '強度分數', 'industry': '產業'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 顯示詳細資料
                st.dataframe(ranking_df)
            
            # 輪動機會
            rotation_data = call_api(f"/industry/rotation?period={period}")
            
            if rotation_data and rotation_data.get("success"):
                st.subheader("🔄 輪動機會")
                
                opportunities = rotation_data["data"].get("rotation_opportunities", [])
                
                if opportunities:
                    for opp in opportunities:
                        with st.expander(f"{opp['from_industry']} → {opp['to_industry']}"):
                            st.write(f"**信號強度**: {opp['signal_strength']}")
                            st.write(f"**預期報酬**: {opp['expected_return']}")
                            st.write(f"**風險等級**: {opp['risk_level']}")
                            st.write(f"**原因**: {opp['reason']}")
                else:
                    st.info("目前沒有輪動機會")


def concept_rotation_page():
    """概念股輪動分析頁面"""
    st.markdown('<div class="main-header"><h1>💡 概念股輪動分析</h1></div>', unsafe_allow_html=True)
    
    period = st.selectbox("選擇分析期間", ["3mo", "6mo", "1y"], index=1)
    
    if st.button("開始分析"):
        with st.spinner("正在分析..."):
            # 概念股排名
            concept_data = call_api(f"/concept/ranking?period={period}")
            
            if concept_data and concept_data.get("success"):
                st.subheader("📊 概念股熱度排名")
                
                concept_df = pd.DataFrame(concept_data["data"])
                
                # 建立圖表
                fig = px.bar(
                    concept_df,
                    x='concept',
                    y='heat_score',
                    color='trend',
                    title='概念股熱度排名',
                    labels={'heat_score': '熱度分數', 'concept': '概念股'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 顯示詳細資料
                st.dataframe(concept_df)
            
            # 熱門概念股
            hot_concepts = call_api(f"/concept/hot?period={period}&min_heat=0.6")
            
            if hot_concepts and hot_concepts.get("success"):
                st.subheader("🔥 熱門概念股")
                
                for concept in hot_concepts["data"]:
                    with st.expander(f"{concept['concept']} (熱度: {concept['heat_score']:.2f})"):
                        st.write(f"**描述**: {concept['description']}")
                        st.write(f"**趨勢**: {concept['trend']}")
                        st.write(f"**股票數**: {len(concept['stocks'])}")
                        
                        # 顯示概念股列表
                        if concept['stocks']:
                            stock_df = pd.DataFrame(concept['stocks'])
                            st.dataframe(stock_df)


def ai_summary_page():
    """AI 選股摘要頁面"""
    st.markdown('<div class="main-header"><h1>🤖 AI 選股摘要</h1></div>', unsafe_allow_html=True)
    
    top_n = st.number_input("返回前 N 名", min_value=1, max_value=50, value=10)
    
    if st.button("生成 AI 摘要"):
        with st.spinner("正在生成 AI 摘要..."):
            result = call_api("/ai/summary", method="POST", params={"top_n": top_n})
            
            if result and result.get("success"):
                data = result["data"]
                
                # 執行摘要
                st.subheader("📋 執行摘要")
                st.info(data.get("executive_summary", "N/A"))
                
                # 投資建議
                st.subheader("💡 投資建議")
                advice = data.get("investment_advice", {})
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("市場建議", advice.get("market_advice", "N/A"))
                
                with col2:
                    st.metric("建議部位", advice.get("position_size", "N/A"))
                
                with col3:
                    st.metric("整體策略", advice.get("overall_strategy", "N/A"))
                
                # 選股推薦
                st.subheader("⭐ 選股推薦")
                recommendations = advice.get("stock_recommendations", [])
                
                if recommendations:
                    rec_df = pd.DataFrame(recommendations)
                    st.dataframe(rec_df)
                
                # 風險提示
                st.subheader("⚠️ 風險提示")
                warnings = data.get("risk_warnings", [])
                
                for warning in warnings:
                    st.warning(warning)


def backtest_page():
    """回測頁面"""
    st.markdown('<div class="main-header"><h1>📊 回測分析</h1></div>', unsafe_allow_html=True)
    
    # 取得可用策略
    strategies_data = call_api("/backtest/strategies")
    
    if strategies_data and strategies_data.get("success"):
        strategies = strategies_data["data"]
        
        st.subheader("📈 選擇策略")
        
        strategy_name = st.selectbox("選擇策略", list(strategies.keys()))
        
        if strategy_name:
            strategy_info = strategies[strategy_name]
            st.write(f"**策略描述**: {strategy_info.get('description', 'N/A')}")
        
        # Walk-Forward 驗證
        st.subheader("🔄 Walk-Forward 驗證")
        
        stock_id = st.text_input("股票代碼", "2330.TW")
        train_window = st.number_input("訓練窗口 (交易日)", min_value=60, max_value=504, value=252)
        test_window = st.number_input("測試窗口 (交易日)", min_value=21, max_value=126, value=63)
        step_size = st.number_input("步進大小 (交易日)", min_value=1, max_value=63, value=21)
        total_years = st.number_input("總回測年數", min_value=1, max_value=10, value=5)
        
        if st.button("開始 Walk-Forward 驗證"):
            with st.spinner("正在驗證..."):
                result = call_api(
                    "/backtest/walk-forward",
                    method="POST",
                    params={
                        "stock_id": stock_id,
                        "strategy_name": strategy_name,
                        "train_window": train_window,
                        "test_window": test_window,
                        "step_size": step_size,
                        "total_years": total_years
                    }
                )
                
                if result and result.get("success"):
                    data = result["data"]
                    
                    st.subheader("📊 Walk-Forward 驗證結果")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("平均報酬率", data.get("avg_return", "N/A"))
                    
                    with col2:
                        st.metric("平均最大回撤", data.get("avg_max_drawdown", "N/A"))
                    
                    with col3:
                        st.metric("平均勝率", data.get("avg_win_rate", "N/A"))
                    
                    with col4:
                        st.metric("平均夏普比率", data.get("avg_sharpe_ratio", "N/A"))


def portfolio_page():
    """虛擬倉位頁面"""
    st.markdown('<div class="main-header"><h1>💼 虛擬倉位管理</h1></div>', unsafe_allow_html=True)
    
    # 取得持倉列表
    positions_data = call_api("/portfolio/positions")
    
    if positions_data and positions_data.get("success"):
        positions = positions_data["data"]
        
        if positions:
            st.subheader("📊 目前持倉")
            
            positions_df = pd.DataFrame(positions)
            st.dataframe(positions_df)
            
            # 計算總資產
            total_value = sum([p.get("market_value", 0) for p in positions])
            st.metric("總資產", f"NT$ {total_value:,.2f}")
        else:
            st.info("目前沒有持倉")
    
    # 交易功能
    st.subheader("💹 交易功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**買入**")
        buy_stock = st.text_input("股票代碼", key="buy_stock")
        buy_shares = st.number_input("股數", min_value=1, value=1000, key="buy_shares")
        
        if st.button("買入"):
            if buy_stock:
                result = call_api("/portfolio/buy", method="POST", data={
                    "stock_id": buy_stock,
                    "shares": buy_shares
                })
                
                if result and result.get("success"):
                    st.success(f"成功買入 {buy_stock} {buy_shares} 股")
                else:
                    st.error("買入失敗")
    
    with col2:
        st.write("**賣出**")
        sell_stock = st.text_input("股票代碼", key="sell_stock")
        sell_shares = st.number_input("股數", min_value=1, value=1000, key="sell_shares")
        
        if st.button("賣出"):
            if sell_stock:
                result = call_api("/portfolio/sell", method="POST", data={
                    "stock_id": sell_stock,
                    "shares": sell_shares
                })
                
                if result and result.get("success"):
                    st.success(f"成功賣出 {sell_stock} {sell_shares} 股")
                else:
                    st.error("賣出失敗")


# 主程式
def main():
    """主程式"""
    # 側邊欄選單
    st.sidebar.title("📊 台灣股票分析工具")
    
    page = st.sidebar.selectbox(
        "選擇頁面",
        ["市場總覽", "個股分析", "多因子選股", "產業輪動分析", "概念股輪動分析", "AI 選股摘要", "回測分析", "虛擬倉位"]
    )
    
    # 根據選擇顯示頁面
    if page == "市場總覽":
        market_overview_page()
    elif page == "個股分析":
        stock_analysis_page()
    elif page == "多因子選股":
        screener_page()
    elif page == "產業輪動分析":
        industry_rotation_page()
    elif page == "概念股輪動分析":
        concept_rotation_page()
    elif page == "AI 選股摘要":
        ai_summary_page()
    elif page == "回測分析":
        backtest_page()
    elif page == "虛擬倉位":
        portfolio_page()
    
    # 側邊欄資訊
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 功能說明")
    st.sidebar.markdown("""
    - **市場總覽**: 查看市場狀態和產業輪動
    - **個股分析**: 分析單一股票
    - **多因子選股**: 多因子選股篩選
    - **產業輪動分析**: 追蹤產業強度變化
    - **概念股輪動分析**: 追蹤熱門概念股
    - **AI 選股摘要**: AI 生成選股報告
    - **回測分析**: Walk-Forward 驗證
    - **虛擬倉位**: 管理虛擬投資
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 相關連結")
    st.sidebar.markdown("""
    - [API 文件](http://localhost:9999/docs)
    - [Web 介面](http://localhost:9999/app)
    - [GitHub](https://github.com/b3401069-ops/taiwan-stock-analysis)
    """)


if __name__ == "__main__":
    main()
