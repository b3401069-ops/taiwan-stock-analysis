"""
台灣股票分析工具 - 自動排程服務
內建排程器，自動產生報告、檢查警報
"""
import threading
import time
from datetime import datetime, timedelta
from loguru import logger
from typing import Dict, List, Callable, Optional
import schedule


class SchedulerService:
    """排程服務"""

    def __init__(self):
        self.is_running = False
        self.thread = None
        self.jobs = []
        
        # 預設排程
        self._setup_default_jobs()

    def _setup_default_jobs(self):
        """設定預設排程"""
        # 每週一早上 9 點產生每週報告
        schedule.every().monday.at("09:00").do(self._weekly_report_job)
        
        # 每天下午 5 點產生每日報告
        schedule.every().day.at("17:00").do(self._daily_report_job)
        
        # 每天早上 9 點檢查停損停利
        schedule.every().day.at("09:00").do(self._check_alerts_job)
        
        # 每天下午 3 點檢查停損停利（收盤後）
        schedule.every().day.at("15:30").do(self._check_alerts_job)
        
        # 每月報告改為每週一執行（模擬每月）
        # schedule 套件不支援每月排程，改用每週執行
        schedule.every().monday.at("10:00").do(self._monthly_report_job)
        
        logger.info("排程服務初始化完成")

    def start(self):
        """啟動排程服務"""
        if self.is_running:
            logger.warning("排程服務已在運行中")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("✅ 排程服務已啟動")
        self._log_scheduled_jobs()

    def stop(self):
        """停止排程服務"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        schedule.clear()
        logger.info("排程服務已停止")

    def _run_scheduler(self):
        """運行排程器"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次
            except Exception as e:
                logger.error(f"排程執行錯誤: {e}")
                time.sleep(60)

    def _log_scheduled_jobs(self):
        """記錄排程任務"""
        jobs = schedule.get_jobs()
        logger.info(f"已排程 {len(jobs)} 個任務:")
        for job in jobs:
            logger.info(f"  • {job.job_func.__name__}: {job.next_run}")

    def _weekly_report_job(self):
        """每週報告任務"""
        try:
            logger.info("⏰ 開始產生每週研究報告...")
            
            from analysis.research_report import get_research_report_generator
            generator = get_research_report_generator()
            
            result = generator.generate_portfolio_report("weekly")
            
            if result.get("success"):
                report = result["data"]
                generator._save_report(report, "weekly")
                
                summary = report.get("summary", {})
                logger.info(f"✅ 每週報告已產生")
                logger.info(f"   持股數量: {summary.get('total_positions', 0)} 檔")
                logger.info(f"   平均報酬: {summary.get('average_return', 0):.2f}%")
                
                # 可以在這裡加入通知功能（Email、LINE 等）
                self._send_notification("每週報告", report)
            else:
                logger.error(f"❌ 每週報告產生失敗: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"每週報告任務失敗: {e}")

    def _daily_report_job(self):
        """每日報告任務"""
        try:
            logger.info("⏰ 開始產生每日研究報告...")
            
            from analysis.research_report import get_research_report_generator
            generator = get_research_report_generator()
            
            result = generator.generate_portfolio_report("daily")
            
            if result.get("success"):
                report = result["data"]
                generator._save_report(report, "daily")
                logger.info(f"✅ 每日報告已產生")
            else:
                logger.error(f"❌ 每日報告產生失敗: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"每日報告任務失敗: {e}")

    def _monthly_report_job(self):
        """每月報告任務"""
        try:
            logger.info("⏰ 開始產生每月研究報告...")
            
            from analysis.research_report import get_research_report_generator
            generator = get_research_report_generator()
            
            result = generator.generate_portfolio_report("monthly")
            
            if result.get("success"):
                report = result["data"]
                generator._save_report(report, "monthly")
                logger.info(f"✅ 每月報告已產生")
            else:
                logger.error(f"❌ 每月報告產生失敗: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"每月報告任務失敗: {e}")

    def _check_alerts_job(self):
        """檢查警報任務"""
        try:
            logger.info("⏰ 開始檢查停損停利警報...")
            
            from analysis.virtual_portfolio import get_virtual_portfolio
            portfolio = get_virtual_portfolio()
            
            alerts = portfolio.check_stop_loss_and_target()
            
            if alerts:
                logger.warning(f"⚠️ 發現 {len(alerts)} 個警報:")
                for alert in alerts:
                    logger.warning(f"   • {alert['message']}")
                
                # 可以在這裡加入通知功能
                self._send_alert_notification(alerts)
            else:
                logger.info("✅ 目前沒有警報")
                
        except Exception as e:
            logger.error(f"檢查警報任務失敗: {e}")

    def _send_notification(self, title: str, report: Dict):
        """
        發送通知（可擴展為 Email、LINE 等）
        
        Args:
            title: 通知標題
            report: 報告資料
        """
        try:
            # 目前只記錄日誌
            # 未來可以擴展：
            # - Email 通知
            # - LINE Notify
            # - Telegram Bot
            # - Slack Webhook
            
            summary = report.get("summary", {})
            message = f"""
{title} 已產生

持股數量: {summary.get('total_positions', 0)} 檔
平均報酬: {summary.get('average_return', 0):.2f}%
總損益: {summary.get('total_profit_loss', 0):+,.0f} 元
            """
            
            logger.info(f"📧 通知: {title}")
            logger.info(message)
            
        except Exception as e:
            logger.error(f"發送通知失敗: {e}")

    def _send_alert_notification(self, alerts: List[Dict]):
        """
        發送警報通知
        
        Args:
            alerts: 警報列表
        """
        try:
            message = "⚠️ 停損停利警報\n\n"
            for alert in alerts:
                message += f"• {alert['message']}\n"
            
            logger.warning(f"📧 警報通知:")
            logger.warning(message)
            
        except Exception as e:
            logger.error(f"發送警報通知失敗: {e}")

    def add_custom_job(self, job_func: Callable, schedule_time: str, 
                       job_name: str = "custom_job"):
        """
        新增自訂排程任務
        
        Args:
            job_func: 任務函數
            schedule_time: 排程時間 (例如: "09:00", "monday", "1st")
            job_name: 任務名稱
        """
        try:
            # 解析排程時間
            if ":" in schedule_time:
                # 每天特定時間
                schedule.every().day.at(schedule_time).do(job_func)
            elif schedule_time.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                # 每週特定天
                getattr(schedule.every(), schedule_time.lower()).at("09:00").do(job_func)
            else:
                logger.warning(f"不支援的排程時間: {schedule_time}")
                return
            
            logger.info(f"✅ 新增排程任務: {job_name} @ {schedule_time}")
            
        except Exception as e:
            logger.error(f"新增排程任務失敗: {e}")

    def get_scheduled_jobs(self) -> List[Dict]:
        """取得所有排程任務"""
        jobs = []
        for job in schedule.get_jobs():
            jobs.append({
                "name": job.job_func.__name__,
                "next_run": str(job.next_run),
                "last_run": str(job.last_run) if job.last_run else "Never"
            })
        return jobs

    def run_job_now(self, job_name: str) -> Dict:
        """
        立即執行指定任務
        
        Args:
            job_name: 任務名稱
            
        Returns:
            執行結果
        """
        try:
            job_map = {
                "weekly_report": self._weekly_report_job,
                "daily_report": self._daily_report_job,
                "monthly_report": self._monthly_report_job,
                "check_alerts": self._check_alerts_job
            }
            
            if job_name not in job_map:
                return {"success": False, "error": f"未知任務: {job_name}"}
            
            logger.info(f"🔄 立即執行任務: {job_name}")
            job_map[job_name]()
            
            return {"success": True, "message": f"任務 {job_name} 已執行"}
            
        except Exception as e:
            logger.error(f"執行任務失敗: {e}")
            return {"success": False, "error": str(e)}


# 全局實例
_scheduler = None


def get_scheduler_service() -> SchedulerService:
    """取得排程服務單例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler
