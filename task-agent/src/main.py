#!/usr/bin/env python3
"""
TradeMind Task Agent - AGX Xavier
Job Scheduling and Distribution Agent
"""

import os
import sys
import json
import time
import asyncio
import signal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pika
import redis
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Config


# Pydantic models
class TaskRequest(BaseModel):
    task_type: str
    symbol: Optional[str] = None
    symbols: Optional[List[str]] = None
    timeframe: Optional[str] = "1d"
    indicators: Optional[List[str]] = None
    factors: Optional[List[str]] = None
    strategy_id: Optional[str] = None
    strategy_params: Optional[Dict[str, Any]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    priority: int = 5


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskAgent:
    """Task Scheduling and Distribution Agent"""
    
    def __init__(self):
        self.config = Config()
        self.agent_id = os.getenv('AGENT_ID', 'task-agent-01')
        self.agent_type = os.getenv('AGENT_TYPE', 'task')
        
        self.running = False
        self.redis_client: Optional[redis.Redis] = None
        self.rabbitmq_connection: Optional[pika.BlockingConnection] = None
        self.rabbitmq_channel: Optional[pika.channel.Channel] = None
        
        # Task tracking
        self.tasks: Dict[str, Dict[str, Any]] = {}
        
        # Scheduler
        self.scheduler = AsyncIOScheduler()
        
        # FastAPI app
        self.app = FastAPI(
            title="TradeMind Task Agent",
            description="Job Scheduling and Distribution for TradeMind",
            version="1.0.0"
        )
        self._setup_routes()
        
        logger.info(f"Task Agent {self.agent_id} initialized")
    
    def connect_redis(self) -> bool:
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    def connect_rabbitmq(self) -> bool:
        """Connect to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                self.config.rabbitmq_user,
                self.config.rabbitmq_pass
            )
            parameters = pika.ConnectionParameters(
                host=self.config.rabbitmq_host,
                port=self.config.rabbitmq_port,
                virtual_host=self.config.rabbitmq_vhost,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.rabbitmq_connection = pika.BlockingConnection(parameters)
            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            
            # Declare all queues
            queues = ['indicator_tasks', 'factor_tasks', 'backtest_tasks', 
                     'indicator_results', 'factor_results', 'backtest_results']
            for queue in queues:
                self.rabbitmq_channel.queue_declare(queue=queue, durable=True)
            
            logger.info(f"Connected to RabbitMQ at {self.config.rabbitmq_host}:{self.config.rabbitmq_port}")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}")
            return False
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'status': 'healthy' if self.running else 'stopped',
                'timestamp': datetime.now().isoformat()
            }
        
        @self.app.post("/tasks/indicator", response_model=TaskResponse)
        async def create_indicator_task(request: TaskRequest):
            """Create technical indicator calculation task"""
            task_id = str(uuid4())
            
            task = {
                'task_id': task_id,
                'task_type': 'indicator',
                'symbol': request.symbol or 'AAPL',
                'timeframe': request.timeframe or '1d',
                'indicators': request.indicators or ['sma', 'ema', 'rsi', 'macd'],
                'priority': request.priority,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            self.tasks[task_id] = task
            self._publish_task('indicator_tasks', task)
            
            return TaskResponse(
                task_id=task_id,
                status='queued',
                message='Indicator task queued for processing'
            )
        
        @self.app.post("/tasks/factor", response_model=TaskResponse)
        async def create_factor_task(request: TaskRequest):
            """Create factor calculation task"""
            task_id = str(uuid4())
            
            task = {
                'task_id': task_id,
                'task_type': 'factor',
                'symbol': request.symbol or 'AAPL',
                'timeframe': request.timeframe or '1d',
                'factors': request.factors or ['momentum', 'volatility', 'quality'],
                'priority': request.priority,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            self.tasks[task_id] = task
            self._publish_task('factor_tasks', task)
            
            return TaskResponse(
                task_id=task_id,
                status='queued',
                message='Factor task queued for processing'
            )
        
        @self.app.post("/tasks/backtest", response_model=TaskResponse)
        async def create_backtest_task(request: TaskRequest):
            """Create backtest task"""
            task_id = str(uuid4())
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            task = {
                'task_id': task_id,
                'task_type': 'backtest',
                'strategy_id': request.strategy_id or 'ma_cross',
                'symbols': request.symbols or ['AAPL'],
                'start_date': request.start_date or start_date.isoformat(),
                'end_date': request.end_date or end_date.isoformat(),
                'strategy_params': request.strategy_params or {'fast_period': 20, 'slow_period': 50},
                'priority': request.priority,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            self.tasks[task_id] = task
            self._publish_task('backtest_tasks', task)
            
            return TaskResponse(
                task_id=task_id,
                status='queued',
                message='Backtest task queued for processing'
            )
        
        @self.app.get("/tasks/{task_id}", response_model=TaskStatus)
        async def get_task_status(task_id: str):
            """Get task status"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[task_id]
            return TaskStatus(
                task_id=task_id,
                status=task.get('status', 'unknown'),
                progress=task.get('progress', 0.0),
                result=task.get('result'),
                created_at=datetime.fromisoformat(task['created_at']),
                completed_at=datetime.fromisoformat(task['completed_at']) if task.get('completed_at') else None
            )
        
        @self.app.get("/tasks")
        async def list_tasks(status: Optional[str] = None):
            """List all tasks"""
            tasks = []
            for task_id, task in self.tasks.items():
                if status is None or task.get('status') == status:
                    tasks.append({
                        'task_id': task_id,
                        'task_type': task.get('task_type'),
                        'status': task.get('status'),
                        'created_at': task.get('created_at')
                    })
            return {'tasks': tasks, 'total': len(tasks)}
        
        @self.app.delete("/tasks/{task_id}")
        async def cancel_task(task_id: str):
            """Cancel a task"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[task_id]
            if task['status'] in ['completed', 'failed']:
                raise HTTPException(status_code=400, detail="Task already finished")
            
            task['status'] = 'cancelled'
            return {'message': 'Task cancelled'}
    
    def _publish_task(self, queue: str, task: Dict[str, Any]):
        """Publish task to RabbitMQ"""
        if not self.rabbitmq_channel:
            logger.error("RabbitMQ not connected")
            return
        
        try:
            self.rabbitmq_channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(task).encode(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    priority=task.get('priority', 5)
                )
            )
            logger.debug(f"Published task {task['task_id']} to {queue}")
        except Exception as e:
            logger.error(f"Failed to publish task: {e}")
    
    def _consume_results(self):
        """Consume results from workers"""
        if not self.rabbitmq_connection:
            return
        
        def callback(ch, method, properties, body):
            try:
                result = json.loads(body)
                task_id = result.get('task_id')
                
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = result.get('status', 'unknown')
                    self.tasks[task_id]['result'] = result
                    self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
                    
                    # Cache result
                    if self.redis_client:
                        self.redis_client.setex(
                            f"task:{task_id}",
                            3600,  # 1 hour TTL
                            json.dumps(result, default=str)
                        )
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug(f"Received result for task {task_id}")
                
            except Exception as e:
                logger.error(f"Failed to process result: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag)
        
        result_queues = ['indicator_results', 'factor_results', 'backtest_results']
        for queue in result_queues:
            try:
                self.rabbitmq_channel.basic_consume(
                    queue=queue,
                    on_message_callback=callback,
                    auto_ack=False
                )
            except Exception as e:
                logger.error(f"Failed to consume {queue}: {e}")
        
        logger.info("Started consuming results")
        
        try:
            self.rabbitmq_channel.start_consuming()
        except Exception as e:
            logger.error(f"Result consumption stopped: {e}")
    
    def _schedule_cleanup(self):
        """Schedule periodic cleanup of old tasks"""
        self.scheduler.add_job(
            self._cleanup_old_tasks,
            trigger=CronTrigger(hour=0, minute=0),
            id='cleanup_tasks',
            replace_existing=True
        )
    
    def _cleanup_old_tasks(self):
        """Remove old completed tasks"""
        cutoff = datetime.now() - timedelta(days=7)
        to_remove = []
        
        for task_id, task in self.tasks.items():
            created = datetime.fromisoformat(task.get('created_at', '2000-01-01'))
            if created < cutoff and task.get('status') in ['completed', 'failed', 'cancelled']:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old tasks")
    
    def run(self):
        """Run the task agent"""
        self.running = True
        
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("Starting Task Agent...")
        
        if not self.connect_redis():
            logger.error("Failed to connect to Redis, continuing without caching")
        
        if not self.connect_rabbitmq():
            logger.error("Failed to connect to RabbitMQ, exiting")
            sys.exit(1)
        
        # Start result consumer in separate thread
        import threading
        result_thread = threading.Thread(target=self._consume_results, daemon=True)
        result_thread.start()
        
        # Start scheduler
        self.scheduler.start()
        self._schedule_cleanup()
        
        # Start API server
        uvicorn.run(
            self.app,
            host='0.0.0.0',
            port=8080,
            log_level='info'
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.scheduler.shutdown()
        if self.rabbitmq_connection:
            self.rabbitmq_connection.close()
        sys.exit(0)


def main():
    agent = TaskAgent()
    agent.run()


if __name__ == '__main__':
    main()
