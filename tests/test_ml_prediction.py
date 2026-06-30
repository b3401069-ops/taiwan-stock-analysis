"""
ML 預測模組測試
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 模擬股票數據
def create_sample_stock_data(days=100):
    """生成模擬股票數據"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    np.random.seed(42)

    # 生成價格序列
    base_price = 100
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.random.uniform(0, 0.02, days)),
        'low': prices * (1 - np.random.uniform(0, 0.02, days)),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, days)
    }, index=dates)

    return df


class TestMLPrediction:
    """ML 預測測試"""

    def setup_method(self):
        """測試前準備"""
        self.df = create_sample_stock_data(200)

    def test_trend_extrapolate(self):
        """測試趨勢外推"""
        from analysis.ml_prediction import MLPrediction
        ml = MLPrediction()

        result = ml._trend_extrapolate(self.df, 5, "Test")

        assert result['model'] == "Test (趨勢外推)"
        assert len(result['predictions']) == 5
        assert result['trend'] in ['up', 'down']
        assert 'expected_return' in result

    def test_arima_predict(self):
        """測試 ARIMA 預測"""
        from analysis.ml_prediction import MLPrediction
        ml = MLPrediction()

        result = ml._arima_predict(self.df, 5)

        assert result['model'] in ['ARIMA', 'ARIMA (趨勢外推)']
        assert len(result['predictions']) == 5

        # 預測價格應該為正數
        for pred in result['predictions']:
            assert pred['predicted_price'] > 0
            assert pred['confidence_interval']['lower'] >= 0

    def test_lstm_predict(self):
        """測試 LSTM 預測"""
        from analysis.ml_prediction import MLPrediction
        ml = MLPrediction()

        result = ml._lstm_predict(self.df, 5)

        assert 'LSTM' in result['model']
        assert len(result['predictions']) == 5

    def test_xgboost_predict(self):
        """測試 XGBoost 預測"""
        from analysis.ml_prediction import MLPrediction
        ml = MLPrediction()

        result = ml._xgboost_predict(self.df, 5)

        assert 'XGBoost' in result['model'] or 'GradientBoosting' in result['model']
        assert len(result['predictions']) == 5
        assert 'model_info' in result

    def test_ensemble_predict(self):
        """測試集成預測"""
        from analysis.ml_prediction import MLPrediction
        ml = MLPrediction()

        # 創建模擬的單一模型預測
        arima_pred = {
            'model': 'ARIMA',
            'predictions': [
                {'date': '2024-01-01', 'predicted_price': 100, 'confidence_interval': {'lower': 95, 'upper': 105}},
                {'date': '2024-01-02', 'predicted_price': 101, 'confidence_interval': {'lower': 96, 'upper': 106}}
            ],
            'trend': 'up',
            'expected_return': 0.01
        }

        lstm_pred = {
            'model': 'LSTM',
            'predictions': [
                {'date': '2024-01-01', 'predicted_price': 99, 'confidence_interval': {'lower': 94, 'upper': 104}},
                {'date': '2024-01-02', 'predicted_price': 100, 'confidence_interval': {'lower': 95, 'upper': 105}}
            ],
            'trend': 'up',
            'expected_return': 0.01
        }

        xgboost_pred = {
            'model': 'XGBoost',
            'predictions': [
                {'date': '2024-01-01', 'predicted_price': 101, 'confidence_interval': {'lower': 96, 'upper': 106}},
                {'date': '2024-01-02', 'predicted_price': 102, 'confidence_interval': {'lower': 97, 'upper': 107}}
            ],
            'trend': 'up',
            'expected_return': 0.02
        }

        result = ml._ensemble_predict([arima_pred, lstm_pred, xgboost_pred])

        assert result['model'] == 'Ensemble'
        assert len(result['predictions']) == 2
        assert 'model_agreement' in result

    def test_model_performance(self):
        """測試模型性能評估"""
        from analysis.ml_prediction import MLPrediction
        from data.stock_data import StockData

        ml = MLPrediction()
        stock_data = StockData()

        # 準備分割數據
        features = stock_data.prepare_ml_features(self.df)
        split_data = stock_data.split_train_test(features, test_size=0.2)

        result = ml._evaluate_model_performance(split_data)

        assert 'baseline' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
