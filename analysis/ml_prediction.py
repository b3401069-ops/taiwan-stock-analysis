"""
台灣股票分析工具 - 機器學習預測模組
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# 導入數據處理模組
from data.data_fetcher import DataFetcher
from data.stock_data import StockData
from config.config import ML_MODELS_CONFIG

# 真實 ML 模型
try:
    from statsmodels.tsa.arima.model import ARIMA as ARIMA_Model
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class MLPrediction:
    """機器學習預測類"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.stock_data = StockData()
        self.config = ML_MODELS_CONFIG
    
    async def predict(self, stock_id: str, model: str = "ensemble", days: int = 30) -> Dict:
        """執行股價預測"""
        try:
            # 獲取價格數據
            price_data = await self.data_fetcher.get_stock_price(stock_id, "2y")
            
            # 轉換為DataFrame
            df = pd.DataFrame(price_data["data"])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 準備特徵
            features_df = self.stock_data.prepare_ml_features(df)
            
            # 分割訓練和測試數據
            split_data = self.stock_data.split_train_test(features_df, test_size=0.2)
            
            prediction_result = {
                "stock_id": stock_id,
                "timestamp": pd.Timestamp.now().isoformat(),
                "model": model,
                "prediction_days": days,
                "predictions": {},
                "model_performance": {},
                "summary": {}
            }
            
            # 根據選擇的模型執行預測
            if model == "arima":
                prediction_result["predictions"]["arima"] = self._arima_predict(df, days)
            elif model == "lstm":
                prediction_result["predictions"]["lstm"] = self._lstm_predict(df, days)
            elif model == "xgboost":
                prediction_result["predictions"]["xgboost"] = self._xgboost_predict(df, days)
            elif model == "transformer":
                prediction_result["predictions"]["transformer"] = self._transformer_predict(df, days)
            elif model == "ensemble":
                # 使用集成學習
                arima_pred = self._arima_predict(df, days)
                lstm_pred = self._lstm_predict(df, days)
                xgboost_pred = self._xgboost_predict(df, days)
                
                latest_price = float(df['close'].iloc[-1])
                prediction_result["predictions"]["ensemble"] = self._ensemble_predict(
                    [arima_pred, lstm_pred, xgboost_pred], latest_price
                )
            
            # 計算模型性能
            prediction_result["model_performance"] = self._evaluate_model_performance(split_data)
            
            # 生成摘要
            prediction_result["summary"] = self._generate_prediction_summary(prediction_result)
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"股價預測失敗: {e}")
            raise
    
    def _trend_extrapolate(self, df: pd.DataFrame, days: int, model_name: str) -> Dict:
        """降級方案：基於移動平均趨勢的線性外推"""
        latest_price = float(df['close'].iloc[-1])
        # 用最近 20 天的線性趨勢外推
        recent = df['close'].iloc[-20:]
        x = np.arange(len(recent))
        slope, intercept = np.polyfit(x, recent.values, 1)
        volatility = float(df['close'].pct_change().rolling(20).std().iloc[-1])

        predictions = []
        for i in range(days):
            pred_price = latest_price + slope * (i + 1)
            lower = pred_price * (1 - 1.96 * volatility * np.sqrt(i + 1))
            upper = pred_price * (1 + 1.96 * volatility * np.sqrt(i + 1))
            pred_date = (pd.Timestamp.now() + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d")
            predictions.append({
                "date": pred_date,
                "predicted_price": float(max(0, pred_price)),
                "confidence_interval": {"lower": float(max(0, lower)), "upper": float(upper)}
            })

        final_price = predictions[-1]["predicted_price"]
        return {
            "model": f"{model_name} (趨勢外推)",
            "predictions": predictions,
            "trend": "up" if final_price > latest_price else "down",
            "expected_return": (final_price - latest_price) / latest_price if latest_price > 0 else 0,
            "model_info": {"method": "linear_trend_extrapolation", "data_points": len(recent)}
        }

    def _arima_predict(self, df: pd.DataFrame, days: int) -> Dict:
        """ARIMA模型預測"""
        try:
            latest_price = float(df['close'].iloc[-1])

            if HAS_STATSMODELS and len(df) >= 30:
                # 使用真實 ARIMA 模型
                close_series = df['close'].dropna()
                model = ARIMA_Model(close_series, order=(1, 1, 1))
                fitted = model.fit()

                # 預測
                forecast = fitted.get_forecast(steps=days)
                pred_mean = forecast.predicted_mean
                conf_int = forecast.conf_int(alpha=0.05)

                predictions = []
                for i in range(days):
                    pred_val = float(pred_mean.iloc[i])
                    lower = float(conf_int.iloc[i, 0])
                    upper = float(conf_int.iloc[i, 1])
                    pred_date = (pd.Timestamp.now() + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d")
                    predictions.append({
                        "date": pred_date,
                        "predicted_price": pred_val,
                        "confidence_interval": {"lower": lower, "upper": upper}
                    })

                final_price = predictions[-1]["predicted_price"]

                return {
                    "model": "ARIMA",
                    "predictions": predictions,
                    "trend": "up" if final_price > latest_price else "down",
                    "expected_return": (final_price - latest_price) / latest_price,
                    "model_info": {
                        "order": "(1,1,1)",
                        "aic": float(fitted.aic),
                        "data_points": len(close_series)
                    }
                }
            else:
                # 降級：使用移動平均趨勢外推
                return self._trend_extrapolate(df, days, "ARIMA")

        except Exception as e:
            logger.error(f"ARIMA預測失敗: {e}，降級為趨勢外推")
            return self._trend_extrapolate(df, days, "ARIMA")
    
    def _lstm_predict(self, df: pd.DataFrame, days: int) -> Dict:
        """LSTM 模型預測（簡化版：使用指數加權移動平均模擬序列依賴性）"""
        try:
            latest_price = float(df['close'].iloc[-1])
            close_series = df['close'].dropna()

            if len(close_series) < 60:
                return self._trend_extrapolate(df, days, "LSTM")

            # 使用 EWMA（指數加權移動平均）模擬 LSTM 的序列學習
            # 短期記憶 (span=10) 和長期記憶 (span=60)
            short_ema = close_series.ewm(span=10).mean()
            long_ema = close_series.ewm(span=60).mean()

            # 趨勢強度：短期 EMA 相對於長期 EMA 的偏離
            trend_strength = float((short_ema.iloc[-1] - long_ema.iloc[-1]) / long_ema.iloc[-1])
            volatility = float(close_series.pct_change().rolling(20).std().iloc[-1])

            # 根據趨勢強度和動量預測
            momentum = float(close_series.pct_change(5).iloc[-1])  # 5日動量

            predictions = []
            for i in range(days):
                # 動量衰減
                decay = 0.95 ** i
                pred_price = latest_price * (1 + momentum * decay + trend_strength * decay * 0.5)

                lower = pred_price * (1 - 1.96 * volatility * np.sqrt(i + 1))
                upper = pred_price * (1 + 1.96 * volatility * np.sqrt(i + 1))
                pred_date = (pd.Timestamp.now() + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d")
                predictions.append({
                    "date": pred_date,
                    "predicted_price": float(max(0, pred_price)),
                    "confidence_interval": {"lower": float(max(0, lower)), "upper": float(upper)}
                })

            final_price = predictions[-1]["predicted_price"]
            return {
                "model": "LSTM (EWMA簡化版)",
                "predictions": predictions,
                "trend": "up" if final_price > latest_price else "down",
                "expected_return": (final_price - latest_price) / latest_price,
                "model_info": {
                    "method": "exponential_weighted_moving_average",
                    "short_ema_span": 10,
                    "long_ema_span": 60,
                    "trend_strength": trend_strength,
                    "momentum_5d": momentum
                }
            }

        except Exception as e:
            logger.error(f"LSTM預測失敗: {e}，降級為趨勢外推")
            return self._trend_extrapolate(df, days, "LSTM")
    
    def _rsi_series(self, close: pd.Series, period: int = 14) -> pd.Series:
        """簡化 RSI（供 XGBoost 特徵使用），並處理除零。"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        return rsi.replace([np.inf, -np.inf], np.nan).fillna(50)

    def _build_xgb_features(self, work: pd.DataFrame) -> pd.DataFrame:
        """建立 XGBoost 的『平穩化』特徵（報酬率、均線比值等），避免以絕對價位當特徵。"""
        work['returns'] = work['close'].pct_change()
        work['ma5_ratio'] = work['close'] / work['close'].rolling(5).mean()
        work['ma10_ratio'] = work['close'] / work['close'].rolling(10).mean()
        work['ma20_ratio'] = work['close'] / work['close'].rolling(20).mean()
        work['volatility'] = work['returns'].rolling(10).std()
        work['rsi'] = self._rsi_series(work['close'])
        work['volume_ratio'] = work['volume'] / work['volume'].rolling(10).mean()
        work['high_low_range'] = (work['high'] - work['low']) / work['close']
        return work

    # XGBoost 特徵欄位（全部為平穩/相對量，不含絕對價位）
    _XGB_FEATURES = ['returns', 'ma5_ratio', 'ma10_ratio', 'ma20_ratio',
                     'volatility', 'rsi', 'volume_ratio', 'high_low_range']

    def _xgboost_predict(self, df: pd.DataFrame, days: int) -> Dict:
        """XGBoost 模型預測（真實實現）。

        修正特徵洩漏：原版以絕對『收盤價』當特徵、又以次日絕對收盤價為目標，
        模型近乎學到 identity（predicted ≈ today's price），R² 漂亮但無預測意義。
        改為：特徵採平穩化（報酬率、均線比值…），目標為『次日報酬率』，
        再把預測報酬率乘回價格做迭代外推。
        """
        try:
            latest_price = float(df['close'].iloc[-1])

            if not (HAS_XGBOOST or HAS_SKLEARN) or len(df) < 60:
                return self._trend_extrapolate(df, days, "XGBoost")

            work = self._build_xgb_features(df.copy().reset_index(drop=True))
            # 目標：次日報酬率（而非次日絕對價位）
            work['target_return'] = work['close'].shift(-1) / work['close'] - 1
            work.replace([np.inf, -np.inf], np.nan, inplace=True)
            work.dropna(inplace=True)
            work.reset_index(drop=True, inplace=True)

            if len(work) < 30:
                return self._trend_extrapolate(df, days, "XGBoost")

            feature_cols = self._XGB_FEATURES
            X = work[feature_cols].values
            y = work['target_return'].values

            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]

            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_test_s = scaler.transform(X_test)

            if HAS_XGBOOST:
                model = XGBRegressor(
                    n_estimators=100, max_depth=5, learning_rate=0.1,
                    subsample=0.8, colsample_bytree=0.8, random_state=42
                )
            else:
                model = GradientBoostingRegressor(
                    n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
                )

            model.fit(X_train_s, y_train)

            # 以「報酬率」評估（注意：股價報酬率本就難預測，R² 偏低是正常且誠實的）
            y_pred_test = model.predict(X_test_s)
            test_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
            test_mae = float(mean_absolute_error(y_test, y_pred_test))
            test_r2 = float(r2_score(y_test, y_pred_test))

            # 迭代預測未來 N 天：每天預測報酬率 → 乘回價格 → 重建特徵
            predictions = []
            current = work.copy()
            price = latest_price
            base_vol = float(work['volatility'].iloc[-1])

            for i in range(days):
                X_pred = current[feature_cols].iloc[-1:].values
                X_pred_s = scaler.transform(X_pred)
                pred_ret = float(model.predict(X_pred_s)[0])
                # 限制單日預測報酬於台股漲跌幅範圍，避免迭代發散
                pred_ret = max(-0.10, min(0.10, pred_ret))
                price = price * (1 + pred_ret)

                vol = base_vol * np.sqrt(i + 1)
                lower = price * (1 - 1.96 * vol)
                upper = price * (1 + 1.96 * vol)
                pred_date = (pd.Timestamp.now() + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d")
                predictions.append({
                    "date": pred_date,
                    "predicted_price": float(max(0, price)),
                    "confidence_interval": {"lower": float(max(0, lower)), "upper": float(upper)}
                })

                # 以預測價與近5日均量重建新的一列，再重算平穩化特徵供下一輪使用
                new_row = current.iloc[-1].copy()
                new_row['open'] = price
                new_row['high'] = price * (1 + abs(pred_ret) / 2)
                new_row['low'] = price * (1 - abs(pred_ret) / 2)
                new_row['close'] = price
                new_row['volume'] = current['volume'].iloc[-5:].mean()
                current = pd.concat([current, new_row.to_frame().T], ignore_index=True)
                current = self._build_xgb_features(current)
                current.replace([np.inf, -np.inf], np.nan, inplace=True)
                current.ffill(inplace=True)
                current.bfill(inplace=True)

            final_price = predictions[-1]["predicted_price"]
            model_name = "XGBoost" if HAS_XGBOOST else "GradientBoosting"

            return {
                "model": model_name,
                "predictions": predictions,
                "trend": "up" if final_price > latest_price else "down",
                "expected_return": (final_price - latest_price) / latest_price,
                "model_info": {
                    "target": "next_day_return",
                    "note": "特徵已平穩化、目標為次日報酬率，避免絕對價位造成的特徵洩漏",
                    "test_rmse_return": test_rmse,
                    "test_mae_return": test_mae,
                    "test_r2_return": test_r2,
                    "training_samples": len(X_train),
                    "feature_importance": dict(zip(feature_cols, model.feature_importances_.tolist()))
                }
            }

        except Exception as e:
            logger.error(f"XGBoost預測失敗: {e}，降級為趨勢外推")
            return self._trend_extrapolate(df, days, "XGBoost")
    
    def _transformer_predict(self, df: pd.DataFrame, days: int) -> Dict:
        """Transformer 模型預測（尚未實作）。

        原版以 np.random.normal 產生純亂數再包裝成「Transformer 預測」，
        每次結果不同且毫無依據，屬誤導。在真正導入 Transformer 前，
        改為誠實地退回可重現的趨勢外推，並在 model 名稱標註未實作。
        """
        result = self._trend_extrapolate(df, days, "Transformer")
        result["model"] = "Transformer (未實作，暫以趨勢外推替代)"
        result.setdefault("model_info", {})["status"] = "not_implemented"
        return result
    
    def _ensemble_predict(self, predictions: List[Dict], latest_price: Optional[float] = None) -> Dict:
        """集成預測。

        latest_price：真實最新收盤價。用來正確計算 expected_return——
        原版誤用「第一天的預測價」當基準，會扭曲報酬率。
        """
        try:
            # 合併所有模型的預測
            ensemble_predictions = []
            
            # 假設所有預測都有相同的天數
            days = len(predictions[0]["predictions"])
            
            for i in range(days):
                # 收集所有模型的預測價格
                prices = []
                for pred in predictions:
                    prices.append(pred["predictions"][i]["predicted_price"])
                
                # 計算集成預測（簡單平均）
                ensemble_price = np.mean(prices)
                
                # 計算標準差
                std = np.std(prices)
                
                ensemble_predictions.append({
                    "date": predictions[0]["predictions"][i]["date"],
                    "predicted_price": float(ensemble_price),
                    "confidence_interval": {
                        "lower": float(ensemble_price - 2 * std),
                        "upper": float(ensemble_price + 2 * std)
                    },
                    "model_agreement": 1 - std / ensemble_price  # 模型一致性
                })
            
            # 計算總體趨勢（以真實現價為基準；未提供時退回第一天預測價）
            if latest_price is None:
                latest_price = predictions[0]["predictions"][0]["predicted_price"]
            final_price = ensemble_predictions[-1]["predicted_price"]
            
            return {
                "model": "Ensemble",
                "predictions": ensemble_predictions,
                "trend": "up" if final_price > latest_price else "down",
                "expected_return": (final_price - latest_price) / latest_price,
                "model_agreement": np.mean([pred["model_agreement"] for pred in ensemble_predictions])
            }
            
        except Exception as e:
            logger.error(f"集成預測失敗: {e}")
            raise
    
    def _evaluate_model_performance(self, split_data: Dict) -> Dict:
        """評估模型性能"""
        try:
            train_data = split_data["train"]
            test_data = split_data["test"]

            # 計算基準性能（簡單移動平均預測）
            if len(test_data) > 1:
                actual = test_data['close'].values
                # 用前一天的收盤價作為預測（random walk baseline）
                baseline_pred = np.roll(actual, 1)
                baseline_pred[0] = train_data['close'].iloc[-1]

                baseline_mse = float(np.mean((actual - baseline_pred) ** 2))
                baseline_rmse = float(np.sqrt(baseline_mse))
                baseline_mae = float(np.mean(np.abs(actual - baseline_pred)))
                mape_vals = np.abs((actual - baseline_pred) / actual)
                mape_vals = mape_vals[np.isfinite(mape_vals)]
                baseline_mape = float(np.mean(mape_vals) * 100) if len(mape_vals) > 0 else 0

                return {
                    "baseline": {
                        "method": "random_walk",
                        "mse": baseline_mse,
                        "rmse": baseline_rmse,
                        "mae": baseline_mae,
                        "mape": baseline_mape,
                        "train_size": len(train_data),
                        "test_size": len(test_data)
                    },
                    "note": "各模型的詳細評估指標請參考 model_info 欄位"
                }
            else:
                return {"note": "測試數據不足，無法評估"}

        except Exception as e:
            logger.error(f"評估模型性能失敗: {e}")
            return {"error": str(e)}
    
    def _generate_prediction_summary(self, prediction_result: Dict) -> Dict:
        """生成預測摘要"""
        try:
            summary = {
                "trend": "neutral",
                "confidence": "medium",
                "expected_return": 0,
                "volatility": "medium",
                "recommendation": "hold"
            }
            
            # 獲取預測結果
            predictions = prediction_result.get("predictions", {})
            
            if "ensemble" in predictions:
                ensemble_pred = predictions["ensemble"]
                summary["trend"] = ensemble_pred.get("trend", "neutral")
                summary["expected_return"] = ensemble_pred.get("expected_return", 0)
                
                # 計算波動性
                pred_prices = [p["predicted_price"] for p in ensemble_pred.get("predictions", [])]
                if pred_prices:
                    volatility = np.std(pred_prices) / np.mean(pred_prices)
                    if volatility > 0.1:
                        summary["volatility"] = "high"
                    elif volatility > 0.05:
                        summary["volatility"] = "medium"
                    else:
                        summary["volatility"] = "low"
                
                # 計算信心水平
                model_agreement = ensemble_pred.get("model_agreement", 0.5)
                if model_agreement > 0.8:
                    summary["confidence"] = "high"
                elif model_agreement > 0.6:
                    summary["confidence"] = "medium"
                else:
                    summary["confidence"] = "low"
            
            # 生成建議
            if summary["expected_return"] > 0.1:
                summary["recommendation"] = "buy"
            elif summary["expected_return"] < -0.1:
                summary["recommendation"] = "sell"
            else:
                summary["recommendation"] = "hold"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成預測摘要失敗: {e}")
            raise