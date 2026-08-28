#!/usr/bin/env python3
"""
TradeMind Monitor Agent - AGX Xavier
System Monitoring and Health Checks
"""

import os
import sys
import json
import time
import asyncio
import signal
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pika
import redis
from loguru import logger

from .config import Config
from .gpu_monitor import GPUMonitor


class SystemMetrics(BaseModel):
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    gpu_percent: Optional[float] = None
    gpu_memory_used: Optional[float] = None
    gpu_temperature: Optional[float] = None
    network_io: Dict[str, float]
    process_count: int


class ServiceStatus(BaseModel):
    service: str
    status: str
    last_check: str
    uptime_seconds: float
    error_count: int


class MonitorAgent:
    """System Monitoring Agent for TradeMind"""
    
    def __init__(self):
        self.config = Config()
        self.agent_id = os.getenv('AGENT_ID', 'monitor-agent-01')
        self.agent_type = os.getenv('AGENT_TYPE', 'monitor')
        
        self.running = False
        self.redis_client: Optional[redis.Redis] = None
        self.rabbitmq_connection: Optional[pika.BlockingConnection] = None
        self.rabbitmq_channel: Optional[pika.channel.Channel] = None
        
        self.gpu_monitor = GPUMonitor()
        self.service_status: Dict[str, Dict[str, Any]] = {}
        self.metrics_history: List[Dict[str, Any]] = []
        
        # FastAPI app
        self.app = FastAPI(
            title="TradeMind Monitor Agent",
            description="System Monitoring for TradeMind",
            version="1.0.0"
        )
        self._setup_routes()
        
        logger.info(f"Monitor Agent {self.agent_id} initialized")
    
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
            
            # Declare health queue
            self.rabbitmq_channel.queue_declare(queue='health_reports', durable=True)
            
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
        
        @self.app.get("/metrics", response_model=SystemMetrics)
        async def get_current_metrics():
            """Get current system metrics"""
            metrics = self._collect_metrics()
            return SystemMetrics(**metrics)
        
        @self.app.get("/metrics/history")
        async def get_metrics_history(minutes: int = 60):
            """Get metrics history"""
            cutoff = datetime.now() - timedelta(minutes=minutes)
            filtered = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m['timestamp']) > cutoff
            ]
            return {'metrics': filtered, 'count': len(filtered)}
        
        @self.app.get("/services")
        async def get_service_status():
            """Get status of all services"""
            services = []
            for service_name, status in self.service_status.items():
                services.append({
                    'service': service_name,
                    'status': status.get('status', 'unknown'),
                    'last_check': status.get('last_check'),
                    'uptime_seconds': status.get('uptime_seconds', 0),
                    'error_count': status.get('error_count', 0)
                })
            return {'services': services}
        
        @self.app.get("/services/{service_name}")
        async def get_specific_service_status(service_name: str):
            """Get specific service status"""
            if service_name not in self.service_status:
                raise HTTPException(status_code=404, detail="Service not found")
            return self.service_status[service_name]
        
        @self.app.post("/services/{service_name}/check")
        async def trigger_service_check(service_name: str):
            """Trigger manual service check"""
            status = await self._check_service(service_name)
            return status
        
        @self.app.get("/jetson/status")
        async def get_jetson_status():
            """Get AGX Xavier specific status"""
            return {
                'model': 'AGX Xavier',
                'jetpack_version': 'R32.1',
                'cuda_version': '10.0',
                'gpu_info': self.gpu_monitor.get_info(),
                'fan_speed': self._get_fan_speed(),
                'temperatures': self._get_temperatures()
            }
        
        @self.app.websocket("/ws/metrics")
        async def metrics_websocket(websocket: WebSocket):
            """WebSocket for real-time metrics"""
            await websocket.accept()
            try:
                while True:
                    metrics = self._collect_metrics()
                    await websocket.send_json(metrics)
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close()
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network
        net_io = psutil.net_io_counters()
        network_io = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
        
        # Processes
        process_count = len(list(psutil.process_iter()))
        
        # GPU (AGX Xavier)
        gpu_info = self.gpu_monitor.get_metrics()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': round(memory_used_gb, 2),
            'memory_total_gb': round(memory_total_gb, 2),
            'disk_percent': disk_percent,
            'gpu_percent': gpu_info.get('gpu_percent'),
            'gpu_memory_used': gpu_info.get('memory_used'),
            'gpu_temperature': gpu_info.get('temperature'),
            'network_io': network_io,
            'process_count': process_count
        }
        
        # Store in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 10080:  # Keep last week (1 min intervals)
            self.metrics_history = self.metrics_history[-10080:]
        
        # Cache in Redis
        if self.redis_client:
            self.redis_client.setex('system:metrics', 60, json.dumps(metrics))
        
        return metrics
    
    async def _check_service(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        services = {
            'rabbitmq': self._check_rabbitmq,
            'redis': self._check_redis,
            'docker': self._check_docker,
            'indicator-worker': lambda: self._check_worker('indicator'),
            'factor-worker': lambda: self._check_worker('factor'),
            'backtest-worker': lambda: self._check_worker('backtest'),
            'task-agent': lambda: self._check_container('trademind-task-agent'),
            'monitor-agent': lambda: self._check_container('trademind-monitor-agent'),
        }
        
        checker = services.get(service_name)
        if checker:
            result = checker()
            self.service_status[service_name] = result
            return result
        
        return {'service': service_name, 'status': 'unknown', 'error': 'No checker available'}
    
    def _check_rabbitmq(self) -> Dict[str, Any]:
        """Check RabbitMQ health"""
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'exec', 'trademind-rabbitmq', 'rabbitmqctl', 'status'],
                capture_output=True, text=True, timeout=10
            )
            
            return {
                'service': 'rabbitmq',
                'status': 'healthy' if result.returncode == 0 else 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'uptime_seconds': 0,  # Would parse from status output
                'error_count': 0
            }
        except Exception as e:
            return {
                'service': 'rabbitmq',
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'error': str(e),
                'error_count': 1
            }
    
    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    'service': 'redis',
                    'status': 'healthy',
                    'last_check': datetime.now().isoformat(),
                    'uptime_seconds': info.get('uptime_in_seconds', 0),
                    'error_count': 0,
                    'connected_clients': info.get('connected_clients', 0)
                }
            return {'service': 'redis', 'status': 'not_connected'}
        except Exception as e:
            return {
                'service': 'redis',
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'error': str(e),
                'error_count': 1
            }
    
    def _check_docker(self) -> Dict[str, Any]:
        """Check Docker daemon"""
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True, text=True, timeout=10
            )
            
            return {
                'service': 'docker',
                'status': 'healthy' if result.returncode == 0 else 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'uptime_seconds': 0,
                'error_count': 0
            }
        except Exception as e:
            return {
                'service': 'docker',
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'error': str(e),
                'error_count': 1
            }
    
    def _check_worker(self, worker_type: str) -> Dict[str, Any]:
        """Check worker health"""
        try:
            import subprocess
            container_name = f'trademind-{worker_type}-worker'
            result = subprocess.run(
                ['docker', 'inspect', '--format={{.State.Status}}', container_name],
                capture_output=True, text=True, timeout=10
            )
            
            status = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            return {
                'service': f'{worker_type}-worker',
                'status': 'healthy' if status == 'running' else status,
                'last_check': datetime.now().isoformat(),
                'uptime_seconds': 0,
                'error_count': 0
            }
        except Exception as e:
            return {
                'service': f'{worker_type}-worker',
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'error': str(e),
                'error_count': 1
            }
    
    def _check_container(self, container_name: str) -> Dict[str, Any]:
        """Check container health"""
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'inspect', '--format={{.State.Status}}', container_name],
                capture_output=True, text=True, timeout=10
            )
            
            status = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            return {
                'service': container_name,
                'status': 'healthy' if status == 'running' else status,
                'last_check': datetime.now().isoformat(),
                'uptime_seconds': 0,
                'error_count': 0
            }
        except Exception as e:
            return {
                'service': container_name,
                'status': 'error',
                'last_check': datetime.now().isoformat(),
                'error': str(e),
                'error_count': 1
            }
    
    def _get_fan_speed(self) -> Optional[float]:
        """Get fan speed on AGX Xavier"""
        try:
            import subprocess
            result = subprocess.run(
                ['cat', '/sys/devices/pwm-fan/target_pwm'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        return None
    
    def _get_temperatures(self) -> Dict[str, float]:
        """Get system temperatures on AGX Xavier"""
        temps = {}
        try:
            # Try to read thermal zones
            import subprocess
            result = subprocess.run(
                ['cat', '/sys/class/thermal/thermal_zone0/temp'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                temps['cpu'] = float(result.stdout.strip()) / 1000.0
        except:
            pass
        return temps
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        import threading
        
        def loop():
            while self.running:
                try:
                    # Collect metrics
                    metrics = self._collect_metrics()
                    
                    # Check thresholds and alert
                    self._check_thresholds(metrics)
                    
                    # Check services periodically
                    if len(self.metrics_history) % 60 == 0:  # Every minute
                        asyncio.run(self._check_all_services())
                    
                    # Publish health report
                    self._publish_health_report(metrics)
                    
                    time.sleep(10)
                    
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
    
    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check metric thresholds and alert"""
        alerts = []
        
        if metrics['cpu_percent'] > 80:
            alerts.append(f"High CPU usage: {metrics['cpu_percent']:.1f}%")
        
        if metrics['memory_percent'] > 85:
            alerts.append(f"High memory usage: {metrics['memory_percent']:.1f}%")
        
        if metrics['disk_percent'] > 90:
            alerts.append(f"High disk usage: {metrics['disk_percent']:.1f}%")
        
        if alerts:
            logger.warning(f"System alerts: {alerts}")
            if self.redis_client:
                self.redis_client.setex(
                    'system:alerts',
                    300,
                    json.dumps(alerts)
                )
    
    async def _check_all_services(self):
        """Check all services"""
        services = [
            'rabbitmq', 'redis', 'docker',
            'indicator-worker', 'factor-worker', 'backtest-worker',
            'task-agent', 'monitor-agent'
        ]
        
        for service in services:
            await self._check_service(service)
    
    def _publish_health_report(self, metrics: Dict[str, Any]):
        """Publish health report to RabbitMQ"""
        if not self.rabbitmq_channel:
            return
        
        try:
            report = {
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'service_status': self.service_status
            }
            
            self.rabbitmq_channel.basic_publish(
                exchange='',
                routing_key='health_reports',
                body=json.dumps(report).encode()
            )
        except Exception as e:
            logger.error(f"Failed to publish health report: {e}")
    
    def run(self):
        """Run the monitor agent"""
        self.running = True
        
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("Starting Monitor Agent...")
        
        if not self.connect_redis():
            logger.error("Failed to connect to Redis, continuing without caching")
        
        if not self.connect_rabbitmq():
            logger.error("Failed to connect to RabbitMQ, continuing")
        
        # Start monitoring loop
        self._monitoring_loop()
        
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
        if self.rabbitmq_connection:
            self.rabbitmq_connection.close()
        sys.exit(0)


def main():
    agent = MonitorAgent()
    agent.run()


if __name__ == '__main__':
    main()
