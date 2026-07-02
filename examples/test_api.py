"""
台灣股票分析工具 - API測試腳本
"""

import json
import time
from typing import Dict, List

import requests

BASE_URL = "http://localhost:8000/api/v1"


class APITester:
    """API測試類"""

    def __init__(self):
        self.session = requests.Session()
        self.test_results = []

    def test_endpoint(
        self,
        name: str,
        method: str,
        endpoint: str,
        params: Dict = None,
        expected_status: int = 200,
    ) -> bool:
        """測試API端點"""
        try:
            url = f"{BASE_URL}{endpoint}"

            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, params=params)
            else:
                print(f"❌ 不支持的HTTP方法: {method}")
                return False

            success = response.status_code == expected_status

            result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "response_time": response.elapsed.total_seconds(),
            }

            self.test_results.append(result)

            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {name}")
            print(f"   端點: {method} {endpoint}")
            print(f"   狀態碼: {response.status_code} (預期: {expected_status})")
            print(f"   回應時間: {result['response_time']:.3f}秒")

            if not success:
                print(f"   回應內容: {response.text[:200]}...")

            return success

        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            return False

    def run_all_tests(self) -> Dict:
        """執行所有測試"""
        print("台灣股票分析工具 - API測試")
        print("=" * 60)

        # 測試健康檢查
        print("\n1. 健康檢查測試")
        self.test_endpoint("健康檢查", "GET", "/health")

        # 測試股票資料端點
        print("\n2. 股票資料端點測試")
        self.test_endpoint("獲取股票列表", "GET", "/stocks", {"market": "taiwan"})
        self.test_endpoint("獲取股票詳細資訊", "GET", "/stocks/2330.TW")
        self.test_endpoint(
            "獲取股票價格歷史", "GET", "/stocks/2330.TW/price", {"period": "1mo"}
        )
        self.test_endpoint("獲取即時股票價格", "GET", "/stocks/2330.TW/realtime")

        # 測試分析功能端點
        print("\n3. 分析功能端點測試")
        self.test_endpoint("獲取技術分析", "GET", "/analysis/2330.TW/technical")
        self.test_endpoint("獲取基本面分析", "GET", "/analysis/2330.TW/fundamental")
        self.test_endpoint("獲取估值分析", "GET", "/analysis/2330.TW/valuation")
        self.test_endpoint(
            "獲取股價預測",
            "GET",
            "/prediction/2330.TW",
            {"model": "ensemble", "days": 30},
        )

        # 測試建議系統端點
        print("\n4. 建議系統端點測試")
        self.test_endpoint("獲取買賣建議", "GET", "/recommendation/2330.TW")
        self.test_endpoint(
            "獲取投資組合建議",
            "GET",
            "/recommendation/portfolio",
            {"risk_level": "medium", "investment_amount": 1000000},
        )

        # 測試AI Agent端點
        print("\n5. AI Agent端點測試")
        self.test_endpoint(
            "AI Agent對話",
            "POST",
            "/agent/chat",
            {"message": "請分析台積電的投資價值", "agent_type": "openclaw"},
        )
        self.test_endpoint(
            "AI Agent分析報告",
            "GET",
            "/agent/analysis/2330.TW",
            {"agent_type": "openclaw"},
        )

        # 測試國際股市連動分析
        print("\n6. 國際股市連動分析測試")
        self.test_endpoint(
            "獲取國際股市連動分析",
            "GET",
            "/global/correlation",
            {"markets": "taiwan,japan,korea,usa"},
        )

        # 測試券商API端點
        print("\n7. 券商API端點測試")
        self.test_endpoint("獲取券商帳戶資訊", "GET", "/broker/accounts")

        # 測試系統狀態
        print("\n8. 系統狀態測試")
        self.test_endpoint("獲取系統狀態", "GET", "/system/status")

        # 生成測試報告
        return self.generate_report()

    def generate_report(self) -> Dict:
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("測試報告")
        print("=" * 60)

        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - successful_tests

        print(f"\n總測試數: {total_tests}")
        print(f"成功測試: {successful_tests}")
        print(f"失敗測試: {failed_tests}")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")

        # 計算平均回應時間
        response_times = [
            r["response_time"] for r in self.test_results if r["response_time"]
        ]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"平均回應時間: {avg_response_time:.3f}秒")

        # 顯示失敗的測試
        if failed_tests > 0:
            print(f"\n失敗的測試:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result['status_code']}")

        # 顯示回應時間最慢的測試
        print(f"\n回應時間最慢的測試:")
        sorted_results = sorted(
            self.test_results, key=lambda x: x["response_time"], reverse=True
        )
        for result in sorted_results[:3]:
            print(f"  - {result['name']}: {result['response_time']:.3f}秒")

        report = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": successful_tests / total_tests * 100,
            "average_response_time": avg_response_time if response_times else 0,
            "test_results": self.test_results,
        }

        return report


def test_specific_stock(stock_id: str):
    """測試特定股票"""
    print(f"\n測試特定股票: {stock_id}")
    print("=" * 60)

    tester = APITester()

    # 測試基本資料
    print(f"\n1. 基本資料測試")
    tester.test_endpoint(
        f"獲取{stock_id}即時價格", "GET", f"/stocks/{stock_id}/realtime"
    )

    # 測試分析功能
    print(f"\n2. 分析功能測試")
    tester.test_endpoint(
        f"獲取{stock_id}技術分析", "GET", f"/analysis/{stock_id}/technical"
    )
    tester.test_endpoint(
        f"獲取{stock_id}基本面分析", "GET", f"/analysis/{stock_id}/fundamental"
    )
    tester.test_endpoint(
        f"獲取{stock_id}估值分析", "GET", f"/analysis/{stock_id}/valuation"
    )

    # 測試預測和建議
    print(f"\n3. 預測和建議測試")
    tester.test_endpoint(
        f"獲取{stock_id}股價預測",
        "GET",
        f"/prediction/{stock_id}",
        {"model": "ensemble", "days": 30},
    )
    tester.test_endpoint(
        f"獲取{stock_id}買賣建議", "GET", f"/recommendation/{stock_id}"
    )

    # 測試AI Agent
    print(f"\n4. AI Agent測試")
    tester.test_endpoint(
        f"AI Agent分析{stock_id}",
        "POST",
        "/agent/chat",
        {"message": f"請分析{stock_id}的投資價值", "agent_type": "openclaw"},
    )

    return tester.generate_report()


def test_performance(iterations: int = 10):
    """測試API性能"""
    print(f"\n性能測試 ({iterations}次迭代)")
    print("=" * 60)

    session = requests.Session()
    response_times = []

    for i in range(iterations):
        start_time = time.time()

        try:
            response = session.get(f"{BASE_URL}/stocks/2330.TW/realtime")
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            print(
                f"  迭代 {i+1}: {response_time:.3f}秒 (狀態碼: {response.status_code})"
            )

        except Exception as e:
            print(f"  迭代 {i+1}: 失敗 - {e}")

    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        print(f"\n性能統計:")
        print(f"  平均回應時間: {avg_time:.3f}秒")
        print(f"  最短回應時間: {min_time:.3f}秒")
        print(f"  最長回應時間: {max_time:.3f}秒")
        print(f"  成功請求數: {len(response_times)}/{iterations}")


def main():
    """主函數"""
    print("台灣股票分析工具 - API測試工具")
    print("=" * 60)

    # 檢查服務是否運行
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服務未運行，請先啟動服務：python main.py")
            return
    except:
        print("❌ 無法連接到服務，請先啟動服務：python main.py")
        return

    print("✅ 服務已連接")

    # 選擇測試類型
    print("\n請選擇測試類型:")
    print("1. 完整API測試")
    print("2. 特定股票測試")
    print("3. 性能測試")
    print("4. 全部測試")

    choice = input("\n請輸入選擇 (1-4): ").strip()

    if choice == "1":
        tester = APITester()
        report = tester.run_all_tests()

        # 儲存測試報告
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n測試報告已儲存到 test_report.json")

    elif choice == "2":
        stock_id = input("請輸入股票代碼 (例如: 2330.TW): ").strip()
        report = test_specific_stock(stock_id)

        # 儲存測試報告
        with open(
            f"test_report_{stock_id.replace('.', '_')}.json", "w", encoding="utf-8"
        ) as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n測試報告已儲存到 test_report_{stock_id.replace('.', '_')}.json")

    elif choice == "3":
        iterations = int(input("請輸入測試次數 (預設10): ").strip() or "10")
        test_performance(iterations)

    elif choice == "4":
        # 執行所有測試
        tester = APITester()
        report = tester.run_all_tests()

        # 測試特定股票
        test_specific_stock("2330.TW")

        # 性能測試
        test_performance(5)

        # 儲存測試報告
        with open("full_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n完整測試報告已儲存到 full_test_report.json")

    else:
        print("❌ 無效的選擇")


if __name__ == "__main__":
    main()
