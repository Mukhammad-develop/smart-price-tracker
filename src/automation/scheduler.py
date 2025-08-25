import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Any
import logging
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class JobPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class JobResult:
    job_id: str
    status: JobStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_count: int

@dataclass
class ScheduledJob:
    job_id: str
    name: str
    function: Callable
    schedule_type: str  # 'interval', 'daily', 'weekly', 'cron'
    schedule_value: Any  # interval in seconds, time string, or cron expression
    priority: JobPriority
    max_retries: int
    retry_delay: int
    timeout_seconds: int
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    args: tuple
    kwargs: dict

class SmartScheduler:
    """Advanced scheduler with job management, monitoring, and persistence"""
    
    def __init__(self, persistence_file: str = "data/scheduler_state.json"):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.job_results: Dict[str, List[JobResult]] = {}
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        self.persistence_file = persistence_file
        self.max_result_history = 100
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(persistence_file), exist_ok=True)
        
        # Load persisted state
        self._load_state()
        
        logger.info("SmartScheduler initialized")
    
    def add_job(self, 
                job_id: str,
                name: str,
                function: Callable,
                schedule_type: str,
                schedule_value: Any,
                priority: JobPriority = JobPriority.MEDIUM,
                max_retries: int = 3,
                retry_delay: int = 60,
                timeout_seconds: int = 300,
                enabled: bool = True,
                *args, **kwargs) -> bool:
        """Add a new scheduled job"""
        
        if job_id in self.jobs:
            logger.warning(f"Job {job_id} already exists, updating...")
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            function=function,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout_seconds=timeout_seconds,
            enabled=enabled,
            last_run=None,
            next_run=self._calculate_next_run(schedule_type, schedule_value),
            run_count=0,
            success_count=0,
            failure_count=0,
            created_at=datetime.utcnow(),
            args=args,
            kwargs=kwargs
        )
        
        self.jobs[job_id] = job
        self.job_results[job_id] = []
        
        # Add to schedule library
        self._schedule_job(job)
        
        # Persist state
        self._save_state()
        
        logger.info(f"Added job: {name} ({job_id}) - {schedule_type}: {schedule_value}")
        return True
    
    def _schedule_job(self, job: ScheduledJob):
        """Add job to the schedule library"""
        
        if not job.enabled:
            return
        
        try:
            if job.schedule_type == "interval":
                schedule.every(job.schedule_value).seconds.do(
                    self._execute_job_wrapper, job.job_id
                ).tag(job.job_id)
            
            elif job.schedule_type == "daily":
                schedule.every().day.at(job.schedule_value).do(
                    self._execute_job_wrapper, job.job_id
                ).tag(job.job_id)
            
            elif job.schedule_type == "weekly":
                day, time_str = job.schedule_value.split(' ')
                getattr(schedule.every(), day.lower()).at(time_str).do(
                    self._execute_job_wrapper, job.job_id
                ).tag(job.job_id)
            
            elif job.schedule_type == "hourly":
                schedule.every().hour.do(
                    self._execute_job_wrapper, job.job_id
                ).tag(job.job_id)
            
            elif job.schedule_type == "minutes":
                schedule.every(job.schedule_value).minutes.do(
                    self._execute_job_wrapper, job.job_id
                ).tag(job.job_id)
            
            else:
                logger.error(f"Unsupported schedule type: {job.schedule_type}")
                
        except Exception as e:
            logger.error(f"Error scheduling job {job.job_id}: {e}")
    
    def _execute_job_wrapper(self, job_id: str):
        """Wrapper for job execution with error handling and monitoring"""
        
        job = self.jobs.get(job_id)
        if not job or not job.enabled:
            return
        
        start_time = datetime.utcnow()
        result = JobResult(
            job_id=job_id,
            status=JobStatus.RUNNING,
            start_time=start_time,
            end_time=None,
            duration_seconds=None,
            result_data=None,
            error_message=None,
            execution_count=job.run_count + 1
        )
        
        logger.info(f"Starting job: {job.name} ({job_id})")
        
        try:
            # Execute with timeout
            result_data = self._execute_with_timeout(
                job.function, job.timeout_seconds, *job.args, **job.kwargs
            )
            
            # Success
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result.status = JobStatus.COMPLETED
            result.end_time = end_time
            result.duration_seconds = duration
            result.result_data = result_data
            
            # Update job statistics
            job.last_run = start_time
            job.next_run = self._calculate_next_run(job.schedule_type, job.schedule_value)
            job.run_count += 1
            job.success_count += 1
            
            logger.info(f"Job completed successfully: {job.name} ({duration:.2f}s)")
            
        except Exception as e:
            # Failure
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result.status = JobStatus.FAILED
            result.end_time = end_time
            result.duration_seconds = duration
            result.error_message = str(e)
            
            # Update job statistics
            job.last_run = start_time
            job.run_count += 1
            job.failure_count += 1
            
            logger.error(f"Job failed: {job.name} - {str(e)}")
            
            # Retry logic could be implemented here
        
        # Store result
        self.job_results[job_id].append(result)
        
        # Limit result history
        if len(self.job_results[job_id]) > self.max_result_history:
            self.job_results[job_id] = self.job_results[job_id][-self.max_result_history:]
        
        # Persist state
        self._save_state()
    
    def _execute_with_timeout(self, func: Callable, timeout: int, *args, **kwargs):
        """Execute function with timeout"""
        
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            logger.error(f"Job timed out after {timeout} seconds")
            raise TimeoutError(f"Job execution timed out after {timeout} seconds")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def _calculate_next_run(self, schedule_type: str, schedule_value: Any) -> Optional[datetime]:
        """Calculate next run time for a job"""
        
        now = datetime.utcnow()
        
        try:
            if schedule_type == "interval":
                return now + timedelta(seconds=schedule_value)
            elif schedule_type == "minutes":
                return now + timedelta(minutes=schedule_value)
            elif schedule_type == "hourly":
                return now + timedelta(hours=1)
            elif schedule_type == "daily":
                # Parse time string like "14:30"
                hour, minute = map(int, schedule_value.split(':'))
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
            elif schedule_type == "weekly":
                # Parse format like "monday 14:30"
                day_name, time_str = schedule_value.split(' ')
                hour, minute = map(int, time_str.split(':'))
                
                days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                target_day = days.index(day_name.lower())
                current_day = now.weekday()
                
                days_ahead = target_day - current_day
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                
                next_run = now + timedelta(days=days_ahead)
                next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return next_run
            
        except Exception as e:
            logger.error(f"Error calculating next run time: {e}")
        
        return None
    
    def start(self):
        """Start the scheduler"""
        
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        
        # Re-schedule all enabled jobs
        schedule.clear()
        for job in self.jobs.values():
            if job.enabled:
                self._schedule_job(job)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        
        self.running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a specific job"""
        
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].enabled = False
        schedule.clear(job_id)
        self._save_state()
        
        logger.info(f"Paused job: {job_id}")
        return True
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        job.enabled = True
        self._schedule_job(job)
        self._save_state()
        
        logger.info(f"Resumed job: {job_id}")
        return True
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job completely"""
        
        if job_id not in self.jobs:
            return False
        
        schedule.clear(job_id)
        del self.jobs[job_id]
        if job_id in self.job_results:
            del self.job_results[job_id]
        
        self._save_state()
        
        logger.info(f"Removed job: {job_id}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a specific job"""
        
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        recent_results = self.job_results.get(job_id, [])[-5:]  # Last 5 results
        
        return {
            'job_id': job.job_id,
            'name': job.name,
            'enabled': job.enabled,
            'schedule_type': job.schedule_type,
            'schedule_value': job.schedule_value,
            'priority': job.priority.name,
            'last_run': job.last_run.isoformat() if job.last_run else None,
            'next_run': job.next_run.isoformat() if job.next_run else None,
            'run_count': job.run_count,
            'success_count': job.success_count,
            'failure_count': job.failure_count,
            'success_rate': (job.success_count / job.run_count * 100) if job.run_count > 0 else 0,
            'recent_results': [
                {
                    'status': result.status.value,
                    'start_time': result.start_time.isoformat(),
                    'duration': result.duration_seconds,
                    'error': result.error_message
                }
                for result in recent_results
            ]
        }
    
    def get_all_jobs_status(self) -> Dict[str, Any]:
        """Get status for all jobs"""
        
        jobs_status = {}
        for job_id in self.jobs:
            jobs_status[job_id] = self.get_job_status(job_id)
        
        return {
            'total_jobs': len(self.jobs),
            'enabled_jobs': sum(1 for job in self.jobs.values() if job.enabled),
            'running': self.running,
            'jobs': jobs_status
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        
        total_runs = sum(job.run_count for job in self.jobs.values())
        total_successes = sum(job.success_count for job in self.jobs.values())
        total_failures = sum(job.failure_count for job in self.jobs.values())
        
        return {
            'scheduler_running': self.running,
            'total_jobs': len(self.jobs),
            'enabled_jobs': sum(1 for job in self.jobs.values() if job.enabled),
            'total_executions': total_runs,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'overall_success_rate': (total_successes / total_runs * 100) if total_runs > 0 else 0,
            'uptime_start': min((job.created_at for job in self.jobs.values()), default=datetime.utcnow()).isoformat()
        }
    
    def _save_state(self):
        """Persist scheduler state to disk"""
        
        try:
            state = {
                'jobs': {},
                'job_results': {}
            }
            
            # Serialize jobs (excluding function objects)
            for job_id, job in self.jobs.items():
                job_dict = asdict(job)
                # Remove function object (can't serialize)
                job_dict.pop('function', None)
                # Convert datetime objects to ISO strings
                for key, value in job_dict.items():
                    if isinstance(value, datetime):
                        job_dict[key] = value.isoformat() if value else None
                    elif isinstance(value, JobPriority):
                        job_dict[key] = value.name
                
                state['jobs'][job_id] = job_dict
            
            # Serialize job results
            for job_id, results in self.job_results.items():
                state['job_results'][job_id] = []
                for result in results[-10:]:  # Keep last 10 results
                    result_dict = asdict(result)
                    # Convert datetime and enum objects
                    for key, value in result_dict.items():
                        if isinstance(value, datetime):
                            result_dict[key] = value.isoformat() if value else None
                        elif isinstance(value, JobStatus):
                            result_dict[key] = value.value
                    
                    state['job_results'][job_id].append(result_dict)
            
            with open(self.persistence_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving scheduler state: {e}")
    
    def _load_state(self):
        """Load persisted scheduler state from disk"""
        
        try:
            if not os.path.exists(self.persistence_file):
                return
            
            with open(self.persistence_file, 'r') as f:
                state = json.load(f)
            
            # Note: We only load metadata, not the actual function objects
            # Functions need to be re-registered when the scheduler restarts
            
            logger.info(f"Loaded scheduler state with {len(state.get('jobs', {}))} jobs")
            
        except Exception as e:
            logger.error(f"Error loading scheduler state: {e}")
    
    def execute_job_now(self, job_id: str) -> bool:
        """Execute a job immediately (outside of schedule)"""
        
        if job_id not in self.jobs:
            return False
        
        # Execute in a separate thread to avoid blocking
        thread = threading.Thread(
            target=self._execute_job_wrapper,
            args=(job_id,),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Manually triggered job: {job_id}")
        return True 