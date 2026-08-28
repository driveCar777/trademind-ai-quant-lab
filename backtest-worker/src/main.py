#!/usr/bin/env python3
"""
TradeMind Backtest Worker - AGX Xavier
Strategy Backtesting Engine
"""

import os
import sys
import json
import time
import signal
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import numpy as np
import pandas as pd
import redis
import pika
from pika.adapters.blocking_connection import BlockingChannel
from loguru import logger

from .backtest_engine import BacktestEngine, Strategy, Order, Position
from .config import Config


@dataclass
class BacktestTask:
    """Backtest task definition"""
    task_id: str
    strategy_id: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    strategy_params: Dict[str, Any] = field(default_factory=dict)


class BacktestWorker:
    """Backtesting Worker for TradeMind"""
    
    def __init__(self):
        self.config = Config()
        self.worker_id = os.getenv('WORKER_ID', 'backtest-worker-01')
        self.worker_type = os.getenv('WORKER_TYPE', 'backtest')
        
        self.running = False
        self.redis_client: Optional[redis.Redis] = None
        self.rabbitmq_connection: Optional[pika.BlockingConnection] = None
        self.rabbitmq_channel: Optional[BlockingChannel] = None
        
        self.engine = BacktestEngine()
        
        logger.info(f"Backtest Worker {self.worker_id} initialized")
        
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
            
            self.rabbitmq_channel.queue_declare(queue='backtest_tasks', durable=True)
            self.rabbitmq_channel.queue_declare(queue='backtest_results', durable=True)
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
                'capabilities': ['backtest', 'optimization', 'walk_forward'],
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
    
    def fetch_market_data(self, symbols: List[str], 
                          start: datetime, end: datetime) -> Dict[str, pd.DataFrame]:
        """Fetch market data for symbols"""
        data = {}
        
        for symbol in symbols:
            cache_key = f"market_data:{symbol}:1d"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                try:
                    df = pd.read_json(cached_data)
                    data[symbol] = df
                    continue
                except Exception as e:
                    logger.warning(f"Cache parse failed for {symbol}: {e}")
            
            # Fetch from master
            try:
                import requests
                url = f"http://{self.config.master_host}:{self.config.master_port}/api/v1/data"
                params = {
                    'symbol': symbol,
                    'timeframe': '1d',
                    'start': start.isoformat(),
                    'end': end.isoformat()
                }
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    df = pd.DataFrame(result)
                    data[symbol] = df
                    
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
        
        return data
    
    def process_task(self, task: BacktestTask) -> Dict[str, Any]:
        """Process backtest task"""
        logger.info(f"Processing backtest task {task.task_id} for strategy {task.strategy_id}")
        
        start_time = time.time()
        
        try:
            # Fetch data
            data = self.fetch_market_data(task.symbols, task.start_date, task.end_date)
            
            if not data:
                raise ValueError("No market data available")
            
            # Run backtest
            result = self.engine.run(
                data=data,
                strategy_id=task.strategy_id,
                strategy_params=task.strategy_params,
                initial_capital=task.initial_capital,
                commission=task.commission,
                slippage=task.slippage
            )
            
            processing_time = time.time() - start_time
            
            return {
                'task_id': task.task_id,
                'worker_id': self.worker_id,
                'status': 'completed',
                'strategy_id': task.strategy_id,
                'results': result,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Backtest task {task.task_id} failed: {e}")
            return {
                'task_id': task.task_id,
                'worker_id': self.worker_id,
                'status': 'failed',
                'strategy_id': task.strategy_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def on_message(self, ch: BlockingChannel, method, properties, body):
        """Handle incoming task message"""
        try:
            message = json.loads(body)
            logger.debug(f"Received backtest message: {message}")
            
            task = BacktestTask(
                task_id=message.get('task_id'),
                strategy_id=message.get('strategy_id'),
                symbols=message.get('symbols', []),
                start_date=datetime.fromisoformat(message['start_date']),
                end_date=datetime.fromisoformat(message['end_date']),
                initial_capital=message.get('initial_capital', 100000.0),
                commission=message.get('commission', 0.001),
                slippage=message.get('slippage', 0.0005),
                strategy_params=message.get('strategy_params', {})
            )
            
            result = self.process_task(task)
            
            # Save results
            result_path = f"/app/results/{task.task_id}.json"
            with open(result_path, 'w') as f:
                json.dump(result, f, default=str)
            
            # Send result
            ch.basic_publish(
                exchange='',
                routing_key='backtest_results',
                body=json.dumps(result, default=str).encode()
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Backtest task {task.task_id} completed in {result.get('processing_time', 0):.3f}s")
            
        except Exception as e:
            logger.error(f"Backtest message processing failed: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start consuming tasks from queue"""
        if not self.rabbitmq_channel:
            raise RuntimeError("RabbitMQ not connected")
        
        logger.info("Starting to consume backtest tasks...")
        self.rabbitmq_channel.basic_consume(
            queue='backtest_tasks',
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
        
        logger.info("Starting Backtest Worker...")
        
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
    worker = BacktestWorker()
    worker.run()


if __name__ == '__main__':
    main()
