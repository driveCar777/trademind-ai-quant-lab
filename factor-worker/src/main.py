#!/usr/bin/env python3
"""
TradeMind Factor Worker - AGX Xavier
Multi-Factor Calculation Worker
"""

import os
import sys
import json
import time
import signal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import redis
import pika
from pika.adapters.blocking_connection import BlockingChannel
from loguru import logger

from .factors import FactorCalculator, FactorType
from .config import Config


@dataclass
class FactorTask:
    """Factor calculation task"""
    task_id: str
    symbol: str
    timeframe: str
    factors: List[str]
    lookback_period: int = 252
    calculation_date: Optional[datetime] = None


class FactorWorker:
    """Multi-Factor Calculation Worker for TradeMind"""
    
    def __init__(self):
        self.config = Config()
        self.worker_id = os.getenv('WORKER_ID', 'factor-worker-01')
        self.worker_type = os.getenv('WORKER_TYPE', 'factor')
        
        # State
        self.running = False
        self.redis_client: Optional[redis.Redis] = None
        self.rabbitmq_connection: Optional[pika.BlockingConnection] = None
        self.rabbitmq_channel: Optional[BlockingChannel] = None
        
        # Initialize factor calculator
        self.calculator = FactorCalculator()
        
        logger.info(f"Factor Worker {self.worker_id} initialized")
        
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
            
            # Declare queues
            self.rabbitmq_channel.queue_declare(queue='factor_tasks', durable=True)
            self.rabbitmq_channel.queue_declare(queue='factor_results', durable=True)
            
            # Set QoS
            self.rabbitmq_channel.basic_qos(prefetch_count=1)
            
            logger.info(f"Connected to RabbitMQ at {self.config.rabbitmq_host}:{self.config.rabbitmq_port}")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}")
            return False
    
    def register_with_master(self) -> bool:
        """Register worker with master"""
        try:
            import requests
            payload = {
                'worker_id': self.worker_id,
                'worker_type': self.worker_type,
                'status': 'ready',
                'capabilities': self.calculator.get_capabilities(),
                'timestamp': datetime.now().isoformat()
            }
            
            url = f"http://{self.config.master_host}:{self.config.master_port}/api/v1/workers/register"
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Registered with master at {self.config.master_host}")
                return True
            else:
                logger.warning(f"Master registration returned {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Master registration failed: {e}")
            return False
    
    def fetch_market_data(self, symbol: str, timeframe: str,
                          start: Optional[datetime] = None,
                          end: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """Fetch market data"""
        # Try cache first
        cache_key = f"market_data:{symbol}:{timeframe}"
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            try:
                df = pd.read_json(cached_data)
                logger.debug(f"Loaded {len(df)} rows from cache for {symbol}")
                return df
            except Exception as e:
                logger.warning(f"Cache parse failed: {e}")
        
        # Fetch from master
        try:
            import requests
            url = f"http://{self.config.master_host}:{self.config.master_port}/api/v1/data"
            params = {
                'symbol': symbol,
                'timeframe': timeframe,
                'start': start.isoformat() if start else None,
                'end': end.isoformat() if end else None
            }
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
        
        return None
    
    def process_task(self, task: FactorTask) -> Dict[str, Any]:
        """Process a factor calculation task"""
        logger.info(f"Processing task {task.task_id} for {task.symbol}")
        
        start_time = time.time()
        
        try:
            # Fetch market data
            end_date = task.calculation_date or datetime.now()
            start_date = end_date - timedelta(days=task.lookback_period * 2)
            
            data = self.fetch_market_data(task.symbol, task.timeframe, start_date, end_date)
            
            if data is None or len(data) == 0:
                raise ValueError(f"No data available for {task.symbol}")
            
            # Calculate factors
            results = {}
            errors = {}
            
            for factor in task.factors:
                try:
                    factor_result = self.calculator.calculate(data, factor, 
                                                             lookback=task.lookback_period)
                    results[factor] = factor_result
                except Exception as e:
                    logger.error(f"Factor {factor} calculation failed: {e}")
                    errors[factor] = str(e)
            
            # Cache results
            cache_key = f"factors:{task.symbol}:{task.timeframe}"
            self.redis_client.setex(
                cache_key,
                300,  # 5 minutes TTL
                json.dumps(results, default=str)
            )
            
            processing_time = time.time() - start_time
            
            return {
                'task_id': task.task_id,
                'worker_id': self.worker_id,
                'status': 'completed' if len(errors) < len(task.factors) else 'partial_failed',
                'symbol': task.symbol,
                'timeframe': task.timeframe,
                'factors': task.factors,
                'results': results,
                'errors': errors if errors else None,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            return {
                'task_id': task.task_id,
                'worker_id': self.worker_id,
                'status': 'failed',
                'symbol': task.symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def on_message(self, ch: BlockingChannel, method, properties, body):
        """Handle incoming task message"""
        try:
            message = json.loads(body)
            logger.debug(f"Received message: {message}")
            
            task = FactorTask(
                task_id=message.get('task_id'),
                symbol=message.get('symbol'),
                timeframe=message.get('timeframe'),
                factors=message.get('factors', []),
                lookback_period=message.get('lookback_period', 252),
                calculation_date=datetime.fromisoformat(message['calculation_date']) if 'calculation_date' in message else None
            )
            
            result = self.process_task(task)
            
            ch.basic_publish(
                exchange='',
                routing_key='factor_results',
                body=json.dumps(result, default=str).encode()
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Task {task.task_id} completed in {result.get('processing_time', 0):.3f}s")
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start consuming tasks from queue"""
        if not self.rabbitmq_channel:
            raise RuntimeError("RabbitMQ not connected")
        
        logger.info("Starting to consume factor tasks...")
        self.rabbitmq_channel.basic_consume(
            queue='factor_tasks',
            on_message_callback=self.on_message,
            auto_ack=False
        )
        
        try:
            self.rabbitmq_channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.rabbitmq_channel.stop_consuming()
    
    def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            'worker_id': self.worker_id,
            'worker_type': self.worker_type,
            'status': 'healthy' if self.running else 'stopped',
            'redis_connected': self.redis_client is not None and self.redis_client.ping() if self.redis_client else False,
            'rabbitmq_connected': self.rabbitmq_connection is not None and self.rabbitmq_connection.is_open if self.rabbitmq_connection else False,
            'timestamp': datetime.now().isoformat()
        }
    
    def run(self):
        """Main worker loop"""
        self.running = True
        
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("Starting Factor Worker...")
        
        if not self.connect_redis():
            logger.error("Failed to connect to Redis, exiting")
            sys.exit(1)
        
        if not self.connect_rabbitmq():
            logger.error("Failed to connect to RabbitMQ, exiting")
            sys.exit(1)
        
        self.register_with_master()
        
        try:
            self.start_consuming()
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            self.cleanup()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.rabbitmq_channel:
            self.rabbitmq_channel.stop_consuming()
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        
        if self.rabbitmq_channel:
            try:
                self.rabbitmq_channel.close()
            except:
                pass
        
        if self.rabbitmq_connection:
            try:
                self.rabbitmq_connection.close()
            except:
                pass
        
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
        
        logger.info("Cleanup complete")


def main():
    worker = FactorWorker()
    worker.run()


if __name__ == '__main__':
    main()
