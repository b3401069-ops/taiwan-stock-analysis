#!/usr/bin/env python3
"""
每週報告自動產生腳本
可搭配 cron 排程執行

使用方式：
1. 手動執行：python scripts/weekly_report.py
2. Cron 排程：每週一早上 9 點執行
   0 9 * * 1 cd /workspace/project && python scripts/weekly_report.py
"""

import os
import sys

# 加入專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

from loguru import logger

from analysis.research_report import get_research_report_generator


def main():
    """主程式"""
    logger.info("開始產生每週研究報告...")

    try:
        # 取得報告生成器
        generator = get_research_report_generator()

        # 產生每週報告
        result = generator.generate_portfolio_report("weekly")

        if result.get("success"):
            report = result["data"]

            # 儲存報告
            generator._save_report(report, "weekly")

            # 顯示摘要
            summary = report.get("summary", {})
            logger.info(f"報告產生成功！")
            logger.info(f"持股數量：{summary.get('total_positions', 0)} 檔")
            logger.info(f"平均報酬：{summary.get('average_return', 0):.2f}%")
            logger.info(f"總損益：{summary.get('total_profit_loss', 0):+,.0f} 元")

            # 顯示文字報告
            print("\n" + "=" * 60)
            print(report.get("report_text", "無報告內容"))
            print("=" * 60)

            return 0
        else:
            logger.error(f"報告產生失敗：{result.get('error', '未知錯誤')}")
            return 1

    except Exception as e:
        logger.error(f"執行失敗：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
