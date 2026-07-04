"""
台灣股票分析工具 - OpenClaw Agent整合模組
整合富邦證券 SDK 服務，提供完整的股票分析功能
"""

import json
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from loguru import logger

from config.config import get_settings


class OpenClawAgent:
    """OpenClaw Agent整合類"""

    def __init__(self, fubon_service_url: str = None):
        self.settings = get_settings()
        self.api_url = self.settings.OPENCLAW_API_URL
        self.api_key = self.settings.OPENCLAW_API_KEY

        # 富邦服務 URL（另一台電腦的服務地址）
        self.fubon_service_url = fubon_service_url or "http://localhost:6666"

    async def chat(self, message: str) -> Dict:
        """與OpenClaw Agent對話"""
        try:
            # 構建請求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "message": message,
                "context": "stock_analysis",
                "model": "gpt-4",
                "temperature": 0.7,
            }

            # 發送請求
            response = requests.post(
                f"{self.api_url}/chat", headers=headers, json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "model": result.get("model", "gpt-4"),
                    "usage": result.get("usage", {}),
                    "timestamp": result.get("timestamp", ""),
                }
            else:
                # 如果API調用失敗，返回模擬回應
                return self._generate_mock_response(message)

        except Exception as e:
            logger.error(f"OpenClaw Agent對話失敗: {e}")
            return self._generate_mock_response(message)

    async def analyze_stock(self, stock_id: str, include_fubon: bool = True) -> Dict:
        """
        使用OpenClaw Agent分析股票

        Args:
            stock_id: 股票代碼
            include_fubon: 是否包含富邦數據

        Returns:
            完整的股票分析報告（JSON 格式）
        """
        try:
            # 取得富邦數據
            fubon_data = {}
            if include_fubon:
                fubon_data = self._get_fubon_data(stock_id)

            # 構建分析提示（包含富邦數據）
            prompt = self._build_analysis_prompt(stock_id, fubon_data)

            # 調用Agent
            response = await self.chat(prompt)

            # 組合分析結果
            analysis = {
                "success": True,
                "stock_id": stock_id,
                "timestamp": pd.Timestamp.now().isoformat(),
                "agent": "OpenClaw",
                "model": response.get("model", "gpt-4"),
                "analysis": response.get("response", ""),
                "fubon_data": fubon_data,
                "confidence": 0.85,
            }

            return analysis

        except Exception as e:
            logger.error(f"OpenClaw Agent分析股票失敗: {e}")
            return {"success": False, "error": str(e)}

    def _get_fubon_data(self, stock_id: str) -> Dict:
        """從富邦服務取得數據"""
        try:
            # 呼叫富邦服務 API
            response = requests.get(
                f"{self.fubon_service_url}/comprehensive/{stock_id}", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
            else:
                logger.warning(f"富邦服務回應異常: {response.status_code}")
                return {}

        except requests.exceptions.ConnectionError:
            logger.warning(f"無法連接富邦服務: {self.fubon_service_url}")
            return {}
        except Exception as e:
            logger.error(f"取得富邦數據失敗: {e}")
            return {}

    def _build_analysis_prompt(self, stock_id: str, fubon_data: Dict) -> str:
        """構建分析提示"""
        prompt = f"""
請分析台灣股票 {stock_id}，提供以下資訊：
1. 基本面分析
2. 技術面分析
3. 估值分析
4. 產業前景
5. 投資建議

請用繁體中文回答，並提供具體的數據支持。
"""

        # 如果有富邦數據，加入提示
        if fubon_data:
            realtime = fubon_data.get("realtime", {}).get("data", {})
            if realtime:
                price_info = realtime.get("price_info") or realtime.get("raw", {})
                prompt += f"\n目前股價資訊（富邦原始欄位）："
                prompt += f"\n{json.dumps(price_info, ensure_ascii=False, indent=2)}"

            institutional = fubon_data.get("institutional", {}).get("data", {})
            if institutional:
                prompt += f"\n三大法人："
                prompt += f"\n- 外資: {institutional.get('foreign_net', 'N/A')}"
                prompt += f"\n- 投信: {institutional.get('trust_net', 'N/A')}"

        return prompt

    async def get_realtime_quote(self, stock_id: str) -> Dict:
        """取得即時報價"""
        try:
            response = requests.get(
                f"{self.fubon_service_url}/quote/{stock_id}", timeout=5
            )
            return response.json()
        except Exception as e:
            logger.error(f"取得即時報價失敗: {e}")
            return {"success": False, "error": str(e)}

    async def get_financial_analysis(self, stock_id: str) -> Dict:
        """取得財報分析"""
        try:
            # 取得財報數據
            response = requests.get(
                f"{self.fubon_service_url}/financial/{stock_id}?report_type=ratios",
                timeout=10,
            )
            financial_data = response.json()

            # 使用 AI 分析財報
            prompt = f"""
請分析以下股票 {stock_id} 的財務數據：

{json.dumps(financial_data.get('data', {}), indent=2, ensure_ascii=False)}

請提供：
1. 獲利能力分析
2. 財務結構分析
3. 成長性分析
4. 投資價值評估
"""
            analysis = await self.chat(prompt)

            return {
                "success": True,
                "stock_id": stock_id,
                "financial_data": financial_data.get("data", {}),
                "analysis": analysis.get("response", ""),
                "timestamp": pd.Timestamp.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"財報分析失敗: {e}")
            return {"success": False, "error": str(e)}

    async def get_institutional_analysis(self, stock_id: str) -> Dict:
        """取得籌碼面分析"""
        try:
            # 取得法人數據
            inst_response = requests.get(
                f"{self.fubon_service_url}/institutional/{stock_id}", timeout=10
            )
            inst_data = inst_response.json()

            # 取得融資融券數據
            margin_response = requests.get(
                f"{self.fubon_service_url}/margin/{stock_id}", timeout=10
            )
            margin_data = margin_response.json()

            # 使用 AI 分析籌碼
            prompt = f"""
請分析以下股票 {stock_id} 的籌碼面數據：

三大法人：
{json.dumps(inst_data.get('data', {}), indent=2, ensure_ascii=False)}

融資融券：
{json.dumps(margin_data.get('data', {}), indent=2, ensure_ascii=False)}

請提供：
1. 法人動向分析
2. 融資融券分析
3. 籌碼面結論
4. 短期趨勢判斷
"""
            analysis = await self.chat(prompt)

            return {
                "success": True,
                "stock_id": stock_id,
                "institutional_data": inst_data.get("data", {}),
                "margin_data": margin_data.get("data", {}),
                "analysis": analysis.get("response", ""),
                "timestamp": pd.Timestamp.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"籌碼面分析失敗: {e}")
            return {"success": False, "error": str(e)}

    def _generate_mock_response(self, message: str) -> Dict:
        """生成模擬回應"""
        try:
            # 根據消息生成模擬回應
            if "股票" in message or "分析" in message:
                response = "這是一個股票分析的模擬回應。在實際應用中，這裡會連接到OpenClaw Agent API，使用GPT-4模型進行智能分析。"
            elif "建議" in message:
                response = (
                    "這是一個投資建議的模擬回應。請注意，所有投資都有風險，請謹慎評估。"
                )
            else:
                response = "這是一個通用的模擬回應。OpenClaw Agent可以幫助您分析股票市場和提供投資建議。"

            return {
                "success": True,
                "response": response,
                "model": "mock-gpt-4",
                "usage": {
                    "prompt_tokens": len(message),
                    "completion_tokens": len(response),
                    "total_tokens": len(message) + len(response),
                },
                "timestamp": pd.Timestamp.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"生成模擬回應失敗: {e}")
            raise


# 全局實例
_agent = None


def get_openclaw_agent(fubon_service_url: str = None) -> OpenClawAgent:
    """取得 OpenClawAgent 單例"""
    global _agent
    if _agent is None:
        _agent = OpenClawAgent(fubon_service_url)
    return _agent
