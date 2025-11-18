"""
Core Orchestrator: Điều phối toàn bộ hệ thống Supply Chain AI.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import logging

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    logging.warning("schedule library not installed. Scheduling disabled.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Task:
    """Một task trong orchestrator."""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        function: Callable,
        schedule_type: str = 'daily',  # 'daily', 'weekly', 'monthly', 'on_demand'
        dependencies: List[str] = None,
        enabled: bool = True
    ):
        self.task_id = task_id
        self.name = name
        self.function = function
        self.schedule_type = schedule_type
        self.dependencies = dependencies or []
        self.enabled = enabled
        self.last_run = None
        self.next_run = None
        self.status = 'pending'  # 'pending', 'running', 'completed', 'failed'
        self.result = None
        self.error = None


class OSOrchestrator:
    """
    Core Orchestrator: Điều phối toàn bộ hệ thống.
    
    Nhiệm vụ:
    - Điều phối: ETL, Feature Store, Model Training, Inference, RL, Simulation, Cognitive Layer
    - Quản lý lịch chạy (scheduling)
    - Dependency graph
    - Ghi log mọi hành động AI
    """
    
    def __init__(self, logs_dir: str = "logs/os_decisions"):
        """
        Args:
            logs_dir: Thư mục lưu logs
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks: Dict[str, Task] = {}
        self.decision_log: List[Dict] = []
        self.running = False
        
        # Initialize tasks
        self._initialize_tasks()
    
    def _initialize_tasks(self):
        """Khởi tạo các tasks mặc định."""
        # ETL Task
        self.register_task(
            task_id='etl',
            name='ETL Data Processing',
            function=self._run_etl,
            schedule_type='daily',
            dependencies=[]
        )
        
        # Feature Store Task
        self.register_task(
            task_id='feature_store',
            name='Build Feature Store',
            function=self._run_feature_store,
            schedule_type='daily',
            dependencies=['etl']
        )
        
        # Model Training Tasks
        self.register_task(
            task_id='train_logistics_delay',
            name='Train Logistics Delay Model',
            function=self._run_train_logistics_delay,
            schedule_type='weekly',
            dependencies=['feature_store']
        )
        
        self.register_task(
            task_id='train_revenue_forecast',
            name='Train Revenue Forecast Model',
            function=self._run_train_revenue_forecast,
            schedule_type='weekly',
            dependencies=['feature_store']
        )
        
        self.register_task(
            task_id='train_churn',
            name='Train Churn Model',
            function=self._run_train_churn,
            schedule_type='weekly',
            dependencies=['feature_store']
        )
        
        # Model Inference Tasks
        self.register_task(
            task_id='inference_daily',
            name='Daily Model Inference',
            function=self._run_daily_inference,
            schedule_type='daily',
            dependencies=['train_logistics_delay', 'train_revenue_forecast', 'train_churn']
        )
        
        # Cognitive Strategy Task
        self.register_task(
            task_id='cognitive_strategy',
            name='Generate Strategic Recommendations',
            function=self._run_cognitive_strategy,
            schedule_type='daily',
            dependencies=['inference_daily']
        )
        
        # Digital Twin Simulation Task
        self.register_task(
            task_id='digital_twin_simulation',
            name='Digital Twin Simulation',
            function=self._run_digital_twin_simulation,
            schedule_type='on_demand',
            dependencies=[]
        )
    
    def register_task(
        self,
        task_id: str,
        name: str,
        function: Callable,
        schedule_type: str = 'daily',
        dependencies: List[str] = None,
        enabled: bool = True
    ):
        """Đăng ký một task."""
        task = Task(
            task_id=task_id,
            name=name,
            function=function,
            schedule_type=schedule_type,
            dependencies=dependencies or [],
            enabled=enabled
        )
        self.tasks[task_id] = task
        logger.info(f"Registered task: {task_id} ({name})")
    
    def run_task(self, task_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Chạy một task.
        
        Args:
            task_id: ID của task
            force: Bỏ qua dependency check nếu True
            
        Returns:
            Task result
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        
        if not task.enabled:
            return {'status': 'skipped', 'reason': 'Task disabled'}
        
        # Check dependencies
        if not force:
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    raise ValueError(f"Dependency not found: {dep_id}")
                
                dep_task = self.tasks[dep_id]
                if dep_task.status != 'completed':
                    return {
                        'status': 'blocked',
                        'reason': f"Dependency {dep_id} not completed"
                    }
        
        # Run task
        task.status = 'running'
        task.last_run = datetime.now()
        
        try:
            logger.info(f"Running task: {task_id}")
            result = task.function()
            task.status = 'completed'
            task.result = result
            
            # Log decision
            self._log_decision({
                'type': 'task_execution',
                'task_id': task_id,
                'task_name': task.name,
                'status': 'completed',
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'status': 'completed',
                'result': result,
                'task_id': task_id
            }
        
        except Exception as e:
            task.status = 'failed'
            task.error = str(e)
            logger.error(f"Task {task_id} failed: {e}")
            
            self._log_decision({
                'type': 'task_execution',
                'task_id': task_id,
                'task_name': task.name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'status': 'failed',
                'error': str(e),
                'task_id': task_id
            }
    
    def run_pipeline(self, pipeline: List[str]) -> Dict[str, Any]:
        """
        Chạy một pipeline các tasks theo thứ tự.
        
        Args:
            pipeline: List of task IDs
            
        Returns:
            Pipeline results
        """
        results = {}
        
        for task_id in pipeline:
            if task_id not in self.tasks:
                results[task_id] = {'status': 'error', 'error': 'Task not found'}
                continue
            
            result = self.run_task(task_id)
            results[task_id] = result
            
            # Stop if task failed
            if result['status'] == 'failed':
                break
        
        return results
    
    def schedule_tasks(self):
        """Setup scheduling cho các tasks."""
        if not SCHEDULE_AVAILABLE:
            logger.warning("Schedule library not available. Scheduling disabled.")
            return
        
        # Daily tasks
        schedule.every().day.at("02:00").do(self.run_task, 'etl')
        schedule.every().day.at("03:00").do(self.run_task, 'feature_store')
        schedule.every().day.at("04:00").do(self.run_task, 'inference_daily')
        schedule.every().day.at("05:00").do(self.run_task, 'cognitive_strategy')
        
        # Weekly tasks (Monday)
        schedule.every().monday.at("01:00").do(self.run_task, 'train_logistics_delay')
        schedule.every().monday.at("01:30").do(self.run_task, 'train_revenue_forecast')
        schedule.every().monday.at("02:00").do(self.run_task, 'train_churn')
        
        logger.info("Scheduled tasks configured")
    
    def start(self):
        """Bắt đầu orchestrator."""
        self.running = True
        self.schedule_tasks()
        
        logger.info("OS Orchestrator started")
        
        if SCHEDULE_AVAILABLE:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        else:
            logger.warning("Orchestrator started but scheduling is disabled.")
    
    def stop(self):
        """Dừng orchestrator."""
        self.running = False
        logger.info("OS Orchestrator stopped")
    
    def _log_decision(self, decision: Dict):
        """Ghi log decision."""
        self.decision_log.append(decision)
        
        # Save to file
        log_file = self.logs_dir / f"decision_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Load existing logs
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Append new log
        logs.append(decision)
        
        # Save
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    # Task implementations (simplified)
    
    def _run_etl(self) -> Dict:
        """Run ETL."""
        logger.info("Running ETL...")
        # In production, call actual ETL script
        return {'status': 'completed', 'records_processed': 1000}
    
    def _run_feature_store(self) -> Dict:
        """Build Feature Store."""
        logger.info("Building Feature Store...")
        return {'status': 'completed', 'features_created': 50}
    
    def _run_train_logistics_delay(self) -> Dict:
        """Train Logistics Delay Model."""
        logger.info("Training Logistics Delay Model...")
        return {'status': 'completed', 'model_version': 'v1.0'}
    
    def _run_train_revenue_forecast(self) -> Dict:
        """Train Revenue Forecast Model."""
        logger.info("Training Revenue Forecast Model...")
        return {'status': 'completed', 'model_version': 'v1.0'}
    
    def _run_train_churn(self) -> Dict:
        """Train Churn Model."""
        logger.info("Training Churn Model...")
        return {'status': 'completed', 'model_version': 'v1.0'}
    
    def _run_daily_inference(self) -> Dict:
        """Run daily inference."""
        logger.info("Running daily inference...")
        return {'status': 'completed', 'predictions_made': 100}
    
    def _run_cognitive_strategy(self) -> Dict:
        """Generate strategic recommendations."""
        logger.info("Generating strategic recommendations...")
        return {'status': 'completed', 'strategies_generated': 3}
    
    def _run_digital_twin_simulation(self) -> Dict:
        """Run Digital Twin simulation."""
        logger.info("Running Digital Twin simulation...")
        return {'status': 'completed', 'simulation_duration': 168}
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái tổng quan."""
        return {
            'running': self.running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'tasks_status': {
                task_id: {
                    'status': task.status,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None
                }
                for task_id, task in self.tasks.items()
            },
            'total_decisions_logged': len(self.decision_log)
        }

