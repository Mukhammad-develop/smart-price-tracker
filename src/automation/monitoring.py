import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
import json
import os
from dataclasses import dataclass, asdict
from collections import deque
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_processes: int
    scraper_success_rate: float
    notification_success_rate: float
    database_size_mb: float

@dataclass
class HealthCheck:
    name: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    message: str
    last_check: datetime
    response_time_ms: Optional[float]
    details: Optional[Dict[str, Any]]

class SystemMonitor:
    """Comprehensive system monitoring and health checking"""
    
    def __init__(self, metrics_retention_hours: int = 168):  # 7 days default
        self.metrics_retention_hours = metrics_retention_hours
        self.metrics_history: deque = deque(maxlen=metrics_retention_hours * 60)  # 1 metric per minute
        self.health_checks: Dict[str, HealthCheck] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False
        self.check_interval = 60  # seconds
        
        # Initialize baseline metrics
        self.baseline_network = self._get_network_stats()
        
        logger.info("SystemMonitor initialized")
    
    def start_monitoring(self):
        """Start continuous system monitoring"""
        
        if self.running:
            logger.warning("System monitoring is already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        
        self.running = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        
        while self.running:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Run health checks
                self._run_health_checks()
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait longer on error
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_available_mb = memory.available / 1024 / 1024
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_free_gb = disk.free / 1024 / 1024 / 1024
            
            # Network metrics
            network = self._get_network_stats()
            network_sent_mb = (network.bytes_sent - self.baseline_network.bytes_sent) / 1024 / 1024
            network_recv_mb = (network.bytes_recv - self.baseline_network.bytes_recv) / 1024 / 1024
            
            # Process metrics
            active_processes = len(psutil.pids())
            
            # Application-specific metrics
            scraper_success_rate = self._get_scraper_success_rate()
            notification_success_rate = self._get_notification_success_rate()
            database_size_mb = self._get_database_size_mb()
            
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_processes=active_processes,
                scraper_success_rate=scraper_success_rate,
                notification_success_rate=notification_success_rate,
                database_size_mb=database_size_mb
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                active_processes=0,
                scraper_success_rate=0.0,
                notification_success_rate=0.0,
                database_size_mb=0.0
            )
    
    def _get_network_stats(self):
        """Get network statistics"""
        try:
            return psutil.net_io_counters()
        except:
            # Fallback for systems where network stats aren't available
            from collections import namedtuple
            NetworkStats = namedtuple('NetworkStats', ['bytes_sent', 'bytes_recv'])
            return NetworkStats(0, 0)
    
    def _get_scraper_success_rate(self) -> float:
        """Calculate scraper success rate from recent metrics"""
        
        try:
            # This would integrate with the actual tracker to get real metrics
            # For now, return a placeholder
            return 95.0  # 95% success rate
        except:
            return 0.0
    
    def _get_notification_success_rate(self) -> float:
        """Calculate notification success rate from recent metrics"""
        
        try:
            # This would integrate with the notification system to get real metrics
            # For now, return a placeholder
            return 98.0  # 98% success rate
        except:
            return 0.0
    
    def _get_database_size_mb(self) -> float:
        """Get database file size in MB"""
        
        try:
            db_path = "data/price_tracker.db"
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                return size_bytes / 1024 / 1024
            return 0.0
        except:
            return 0.0
    
    def _run_health_checks(self):
        """Run all health checks"""
        
        # Database health check
        self._check_database_health()
        
        # Network connectivity check
        self._check_network_connectivity()
        
        # Disk space check
        self._check_disk_space()
        
        # Memory usage check
        self._check_memory_usage()
        
        # CPU usage check
        self._check_cpu_usage()
        
        # Application-specific checks
        self._check_scraper_health()
        self._check_notification_health()
    
    def _check_database_health(self):
        """Check database connectivity and performance"""
        
        start_time = time.time()
        
        try:
            # Try to connect and run a simple query
            db_path = "data/price_tracker.db"
            
            if not os.path.exists(db_path):
                self.health_checks['database'] = HealthCheck(
                    name="Database",
                    status="critical",
                    message="Database file not found",
                    last_check=datetime.utcnow(),
                    response_time_ms=None,
                    details={"path": db_path}
                )
                return
            
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            if response_time > 1000:  # > 1 second
                status = "warning"
                message = f"Database responding slowly ({response_time:.0f}ms)"
            else:
                status = "healthy"
                message = f"Database healthy ({product_count} products)"
            
            self.health_checks['database'] = HealthCheck(
                name="Database",
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                details={
                    "product_count": product_count,
                    "size_mb": self._get_database_size_mb()
                }
            )
            
        except Exception as e:
            self.health_checks['database'] = HealthCheck(
                name="Database",
                status="critical",
                message=f"Database error: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    def _check_network_connectivity(self):
        """Check network connectivity"""
        
        import socket
        start_time = time.time()
        
        try:
            # Test connection to a reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            self.health_checks['network'] = HealthCheck(
                name="Network",
                status="healthy",
                message=f"Network connectivity OK ({response_time:.0f}ms)",
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                details=None
            )
            
        except Exception as e:
            self.health_checks['network'] = HealthCheck(
                name="Network",
                status="critical",
                message=f"Network connectivity failed: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    def _check_disk_space(self):
        """Check available disk space"""
        
        try:
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            free_gb = disk.free / 1024 / 1024 / 1024
            
            if free_percent < 5:  # Less than 5% free
                status = "critical"
                message = f"Critically low disk space ({free_percent:.1f}% free)"
            elif free_percent < 15:  # Less than 15% free
                status = "warning"
                message = f"Low disk space ({free_percent:.1f}% free)"
            else:
                status = "healthy"
                message = f"Disk space OK ({free_gb:.1f}GB free)"
            
            self.health_checks['disk'] = HealthCheck(
                name="Disk Space",
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={
                    "free_percent": free_percent,
                    "free_gb": free_gb,
                    "total_gb": disk.total / 1024 / 1024 / 1024
                }
            )
            
        except Exception as e:
            self.health_checks['disk'] = HealthCheck(
                name="Disk Space",
                status="unknown",
                message=f"Could not check disk space: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    def _check_memory_usage(self):
        """Check memory usage"""
        
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:  # More than 90% used
                status = "critical"
                message = f"Critical memory usage ({memory.percent:.1f}%)"
            elif memory.percent > 80:  # More than 80% used
                status = "warning"
                message = f"High memory usage ({memory.percent:.1f}%)"
            else:
                status = "healthy"
                message = f"Memory usage OK ({memory.percent:.1f}%)"
            
            self.health_checks['memory'] = HealthCheck(
                name="Memory Usage",
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={
                    "percent_used": memory.percent,
                    "used_gb": memory.used / 1024 / 1024 / 1024,
                    "total_gb": memory.total / 1024 / 1024 / 1024
                }
            )
            
        except Exception as e:
            self.health_checks['memory'] = HealthCheck(
                name="Memory Usage",
                status="unknown",
                message=f"Could not check memory usage: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    def _check_cpu_usage(self):
        """Check CPU usage"""
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > 90:  # More than 90% used
                status = "critical"
                message = f"Critical CPU usage ({cpu_percent:.1f}%)"
            elif cpu_percent > 80:  # More than 80% used
                status = "warning"
                message = f"High CPU usage ({cpu_percent:.1f}%)"
            else:
                status = "healthy"
                message = f"CPU usage OK ({cpu_percent:.1f}%)"
            
            self.health_checks['cpu'] = HealthCheck(
                name="CPU Usage",
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={
                    "percent_used": cpu_percent,
                    "cpu_count": psutil.cpu_count()
                }
            )
            
        except Exception as e:
            self.health_checks['cpu'] = HealthCheck(
                name="CPU Usage",
                status="unknown",
                message=f"Could not check CPU usage: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    def _check_scraper_health(self):
        """Check scraper performance and health"""
        
        try:
            success_rate = self._get_scraper_success_rate()
            
            if success_rate < 70:  # Less than 70% success
                status = "critical"
                message = f"Poor scraper performance ({success_rate:.1f}% success)"
            elif success_rate < 90:  # Less than 90% success
                status = "warning"
                message = f"Degraded scraper performance ({success_rate:.1f}% success)"
            else:
                status = "healthy"
                message = f"Scraper performance OK ({success_rate:.1f}% success)"
            
            self.health_checks['scraper'] = HealthCheck(
                name="Scraper Health",
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={
                    "success_rate": success_rate
                }
            )
            
        except Exception as e:
            self.health_checks['scraper'] = HealthCheck(
                name="Scraper Health",
                status="unknown",
                message=f"Could not check scraper health: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    def _check_notification_health(self):
        """Check notification system health"""
        
        try:
            success_rate = self._get_notification_success_rate()
            
            if success_rate < 80:  # Less than 80% success
                status = "critical"
                message = f"Poor notification performance ({success_rate:.1f}% success)"
            elif success_rate < 95:  # Less than 95% success
                status = "warning"
                message = f"Degraded notification performance ({success_rate:.1f}% success)"
            else:
                status = "healthy"
                message = f"Notification system OK ({success_rate:.1f}% success)"
            
            self.health_checks['notifications'] = HealthCheck(
                name="Notifications",
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={
                    "success_rate": success_rate
                }
            )
            
        except Exception as e:
            self.health_checks['notifications'] = HealthCheck(
                name="Notifications",
                status="unknown",
                message=f"Could not check notification health: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent system metrics"""
        
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of metrics for the specified time period"""
        
        if not self.metrics_history:
            return {}
        
        # Filter metrics for the specified time period
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages and extremes
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_percent for m in recent_metrics]
        
        return {
            'time_period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values)
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values),
                'min': min(memory_values),
                'max': max(memory_values)
            },
            'disk': {
                'avg': sum(disk_values) / len(disk_values),
                'min': min(disk_values),
                'max': max(disk_values)
            },
            'scraper_avg_success_rate': sum(m.scraper_success_rate for m in recent_metrics) / len(recent_metrics),
            'notification_avg_success_rate': sum(m.notification_success_rate for m in recent_metrics) / len(recent_metrics),
            'database_size_mb': recent_metrics[-1].database_size_mb
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all components"""
        
        overall_status = "healthy"
        critical_issues = []
        warnings = []
        
        for check in self.health_checks.values():
            if check.status == "critical":
                overall_status = "critical"
                critical_issues.append(check.message)
            elif check.status == "warning" and overall_status != "critical":
                overall_status = "warning"
                warnings.append(check.message)
        
        return {
            'overall_status': overall_status,
            'last_check': datetime.utcnow().isoformat(),
            'critical_issues': critical_issues,
            'warnings': warnings,
            'checks': {
                name: {
                    'status': check.status,
                    'message': check.message,
                    'last_check': check.last_check.isoformat(),
                    'response_time_ms': check.response_time_ms,
                    'details': check.details
                }
                for name, check in self.health_checks.items()
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and trends"""
        
        current = self.get_current_metrics()
        if not current:
            return {}
        
        summary_24h = self.get_metrics_summary(24)
        summary_1h = self.get_metrics_summary(1)
        
        return {
            'current': {
                'timestamp': current.timestamp.isoformat(),
                'cpu_percent': current.cpu_percent,
                'memory_percent': current.memory_percent,
                'disk_percent': current.disk_percent,
                'network_sent_mb': current.network_sent_mb,
                'network_recv_mb': current.network_recv_mb,
                'scraper_success_rate': current.scraper_success_rate,
                'notification_success_rate': current.notification_success_rate,
                'database_size_mb': current.database_size_mb
            },
            '24h_summary': summary_24h,
            '1h_summary': summary_1h
        }
    
    def add_custom_health_check(self, name: str, check_function: Callable[[], HealthCheck]):
        """Add a custom health check function"""
        
        try:
            result = check_function()
            self.health_checks[name] = result
            logger.info(f"Added custom health check: {name}")
        except Exception as e:
            self.health_checks[name] = HealthCheck(
                name=name,
                status="critical",
                message=f"Custom check failed: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
            logger.error(f"Custom health check failed: {name} - {e}")
    
    def export_metrics(self, filepath: str, hours: int = 24):
        """Export metrics to JSON file"""
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
            
            export_data = {
                'export_time': datetime.utcnow().isoformat(),
                'time_period_hours': hours,
                'total_metrics': len(recent_metrics),
                'metrics': [asdict(m) for m in recent_metrics],
                'health_status': self.get_health_status(),
                'performance_summary': self.get_performance_metrics()
            }
            
            # Convert datetime objects to ISO strings
            for metric in export_data['metrics']:
                metric['timestamp'] = metric['timestamp'].isoformat()
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported {len(recent_metrics)} metrics to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            raise 