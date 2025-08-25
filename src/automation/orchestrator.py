import logging
import signal
import sys
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

from .scheduler import SmartScheduler, JobPriority
from .monitoring import SystemMonitor
from ..core.tracker import PriceTracker
from ..utils.config import Config
from ..notifications.notification_manager import NotificationManager

logger = logging.getLogger(__name__)

class AutomationOrchestrator:
    """Main orchestrator for automated price tracking system"""
    
    def __init__(self, config_file: str = None):
        self.config = Config()
        self.tracker = PriceTracker(self.config)
        self.scheduler = SmartScheduler()
        self.monitor = SystemMonitor()
        self.notification_manager = NotificationManager(self.config)
        
        # State management
        self.running = False
        self.startup_time = datetime.utcnow()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("AutomationOrchestrator initialized")
    
    def start(self):
        """Start the complete automation system"""
        
        if self.running:
            logger.warning("Automation system is already running")
            return
        
        logger.info("🚀 Starting Smart Price Tracker Automation System")
        
        try:
            # Start system monitoring
            self.monitor.start_monitoring()
            logger.info("✅ System monitoring started")
            
            # Setup default jobs
            self._setup_default_jobs()
            logger.info("✅ Default jobs configured")
            
            # Start scheduler
            self.scheduler.start()
            logger.info("✅ Job scheduler started")
            
            # Send startup notification
            self._send_startup_notification()
            
            self.running = True
            logger.info("🎉 Automation system fully operational!")
            
            # Keep the main thread alive
            self._main_loop()
            
        except Exception as e:
            logger.error(f"Failed to start automation system: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the automation system gracefully"""
        
        if not self.running:
            return
        
        logger.info("🛑 Stopping Smart Price Tracker Automation System")
        
        try:
            # Stop scheduler
            self.scheduler.stop()
            logger.info("✅ Scheduler stopped")
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            logger.info("✅ Monitoring stopped")
            
            # Send shutdown notification
            self._send_shutdown_notification()
            
            self.running = False
            logger.info("✅ Automation system stopped gracefully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)
    
    def _main_loop(self):
        """Main loop to keep the system running"""
        
        try:
            while self.running:
                # Check system health periodically
                health_status = self.get_system_health()
                
                # Log critical issues
                if health_status.get('overall_status') == 'critical':
                    critical_issues = health_status.get('critical_issues', [])
                    logger.critical(f"Critical system issues detected: {critical_issues}")
                    
                    # Send critical alert
                    self._send_critical_alert(critical_issues)
                
                # Sleep for a while before next check
                threading.Event().wait(300)  # 5 minutes
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.stop()
    
    def _setup_default_jobs(self):
        """Setup default scheduled jobs"""
        
        # Main price tracking job - runs every hour
        self.scheduler.add_job(
            job_id="main_tracking",
            name="Main Price Tracking",
            function=self._run_main_tracking,
            schedule_type="minutes",
            schedule_value=60,  # Every hour
            priority=JobPriority.HIGH,
            timeout_seconds=1800,  # 30 minutes timeout
            max_retries=2
        )
        
        # Quick price check - runs every 15 minutes for high-priority items
        self.scheduler.add_job(
            job_id="quick_check",
            name="Quick Price Check",
            function=self._run_quick_check,
            schedule_type="minutes",
            schedule_value=15,  # Every 15 minutes
            priority=JobPriority.MEDIUM,
            timeout_seconds=600,  # 10 minutes timeout
            max_retries=1
        )
        
        # Daily data export
        self.scheduler.add_job(
            job_id="daily_export",
            name="Daily Data Export",
            function=self._run_daily_export,
            schedule_type="daily",
            schedule_value="02:00",  # 2 AM
            priority=JobPriority.LOW,
            timeout_seconds=900,  # 15 minutes timeout
            max_retries=2
        )
        
        # Weekly analytics report
        self.scheduler.add_job(
            job_id="weekly_report",
            name="Weekly Analytics Report",
            function=self._send_weekly_report,
            schedule_type="weekly",
            schedule_value="sunday 09:00",  # Sunday 9 AM
            priority=JobPriority.LOW,
            timeout_seconds=600,  # 10 minutes timeout
            max_retries=1
        )
        
        # System health check - runs every 30 minutes
        self.scheduler.add_job(
            job_id="health_check",
            name="System Health Check",
            function=self._run_health_check,
            schedule_type="minutes",
            schedule_value=30,  # Every 30 minutes
            priority=JobPriority.MEDIUM,
            timeout_seconds=300,  # 5 minutes timeout
            max_retries=1
        )
        
        # Database cleanup - runs daily at 3 AM
        self.scheduler.add_job(
            job_id="database_cleanup",
            name="Database Cleanup",
            function=self._run_database_cleanup,
            schedule_type="daily",
            schedule_value="03:00",  # 3 AM
            priority=JobPriority.LOW,
            timeout_seconds=1200,  # 20 minutes timeout
            max_retries=1
        )
        
        logger.info("Default jobs configured successfully")
    
    def _run_main_tracking(self) -> Dict[str, Any]:
        """Main price tracking job"""
        
        logger.info("🔄 Running main price tracking job")
        
        try:
            # Run tracking for all active products
            result = self.tracker.run_tracking(export_after=False)
            
            logger.info(f"Main tracking completed: {result['updated']} updated, {result['failed']} failed")
            
            return {
                'success': True,
                'updated_count': result['updated'],
                'failed_count': result['failed'],
                'total_count': result['total']
            }
            
        except Exception as e:
            logger.error(f"Main tracking job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_quick_check(self) -> Dict[str, Any]:
        """Quick check for high-priority products"""
        
        logger.info("⚡ Running quick price check")
        
        try:
            # Get high-priority products (those with target prices or recent changes)
            products = self.tracker.get_tracked_products()
            priority_products = [
                p for p in products 
                if p.get('target_price') or p.get('notification_enabled', True)
            ]
            
            if not priority_products:
                return {'success': True, 'message': 'No priority products to check'}
            
            # Run tracking for priority products only
            priority_ids = [p['id'] for p in priority_products[:10]]  # Limit to 10
            result = self.tracker.run_tracking(product_ids=priority_ids)
            
            logger.info(f"Quick check completed: {result['updated']} updated, {result['failed']} failed")
            
            return {
                'success': True,
                'checked_count': len(priority_ids),
                'updated_count': result['updated'],
                'failed_count': result['failed']
            }
            
        except Exception as e:
            logger.error(f"Quick check job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_daily_export(self) -> Dict[str, Any]:
        """Daily data export job"""
        
        logger.info("📊 Running daily data export")
        
        try:
            # Run comprehensive export
            export_result = self.tracker.data_manager.run_daily_export()
            
            logger.info(f"Daily export completed: {export_result}")
            
            return {
                'success': True,
                'export_results': export_result
            }
            
        except Exception as e:
            logger.error(f"Daily export job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_weekly_report(self) -> Dict[str, Any]:
        """Send weekly analytics report"""
        
        logger.info("📈 Generating weekly analytics report")
        
        try:
            # Get analytics for the past week
            analytics = self.tracker.get_analytics(days=7)
            
            # Send report via notifications
            self.tracker.notification_manager.send_daily_summary(analytics)
            
            logger.info("Weekly report sent successfully")
            
            return {
                'success': True,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Weekly report job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_health_check(self) -> Dict[str, Any]:
        """System health check job"""
        
        logger.debug("🏥 Running system health check")
        
        try:
            health_status = self.monitor.get_health_status()
            
            # Log warnings and critical issues
            if health_status.get('warnings'):
                logger.warning(f"System warnings: {health_status['warnings']}")
            
            if health_status.get('critical_issues'):
                logger.critical(f"Critical issues: {health_status['critical_issues']}")
                # Send immediate notification for critical issues
                self._send_critical_alert(health_status['critical_issues'])
            
            return {
                'success': True,
                'health_status': health_status
            }
            
        except Exception as e:
            logger.error(f"Health check job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_database_cleanup(self) -> Dict[str, Any]:
        """Database cleanup job"""
        
        logger.info("🧹 Running database cleanup")
        
        try:
            # Cleanup old price history (keep 90 days)
            from ..core.database import db_manager
            from ..models.product import PriceHistory
            from sqlalchemy import and_
            
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            with db_manager.get_session() as session:
                deleted_count = session.query(PriceHistory).filter(
                    PriceHistory.timestamp < cutoff_date
                ).delete()
                session.commit()
            
            logger.info(f"Database cleanup completed: {deleted_count} old records removed")
            
            return {
                'success': True,
                'deleted_records': deleted_count
            }
            
        except Exception as e:
            logger.error(f"Database cleanup job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_startup_notification(self):
        """Send notification when system starts"""
        
        try:
            products_count = len(self.tracker.get_tracked_products())
            
            message = f"""
🚀 Smart Price Tracker Started

System Status: Operational
Tracked Products: {products_count}
Started At: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}

The automated price tracking system is now running and will monitor your products according to the configured schedule.
            """.strip()
            
            self.notification_manager.send_notification(
                title="🚀 Price Tracker Started",
                message=message,
                priority="medium"
            )
            
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    def _send_shutdown_notification(self):
        """Send notification when system shuts down"""
        
        try:
            uptime = datetime.utcnow() - self.startup_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            message = f"""
🛑 Smart Price Tracker Stopped

System Status: Offline
Uptime: {uptime_str}
Stopped At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

The automated price tracking system has been stopped gracefully.
            """.strip()
            
            self.notification_manager.send_notification(
                title="🛑 Price Tracker Stopped",
                message=message,
                priority="medium"
            )
            
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")
    
    def _send_critical_alert(self, issues: List[str]):
        """Send critical system alert"""
        
        try:
            message = f"""
🚨 CRITICAL SYSTEM ALERT

The following critical issues have been detected:

{chr(10).join(f'• {issue}' for issue in issues)}

Please check the system immediately to ensure proper operation.

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            self.notification_manager.send_notification(
                title="🚨 Critical System Alert",
                message=message,
                priority="urgent"
            )
            
        except Exception as e:
            logger.error(f"Failed to send critical alert: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        return {
            'running': self.running,
            'startup_time': self.startup_time.isoformat(),
            'uptime_seconds': (datetime.utcnow() - self.startup_time).total_seconds(),
            'scheduler_status': self.scheduler.get_all_jobs_status(),
            'health_status': self.monitor.get_health_status(),
            'performance_metrics': self.monitor.get_performance_metrics(),
            'tracked_products': len(self.tracker.get_tracked_products()),
            'notification_status': self.tracker.get_notification_status(),
            'export_status': self.tracker.get_export_status()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health summary"""
        
        return self.monitor.get_health_status()
    
    def add_custom_job(self, job_id: str, name: str, function, schedule_type: str, 
                      schedule_value: Any, **kwargs) -> bool:
        """Add a custom scheduled job"""
        
        return self.scheduler.add_job(
            job_id=job_id,
            name=name,
            function=function,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            **kwargs
        )
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a specific job"""
        return self.scheduler.pause_job(job_id)
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        return self.scheduler.resume_job(job_id)
    
    def execute_job_now(self, job_id: str) -> bool:
        """Execute a job immediately"""
        return self.scheduler.execute_job_now(job_id)
    
    def export_system_metrics(self, filepath: str, hours: int = 24):
        """Export system metrics to file"""
        
        try:
            self.monitor.export_metrics(filepath, hours)
            logger.info(f"System metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        return self.scheduler.get_job_status(job_id)
    
    def list_all_jobs(self) -> Dict[str, Any]:
        """List all scheduled jobs"""
        return self.scheduler.get_all_jobs_status()

def main():
    """Main entry point for automation system"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/automation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting Smart Price Tracker Automation System")
    
    try:
        # Create and start orchestrator
        orchestrator = AutomationOrchestrator()
        orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 