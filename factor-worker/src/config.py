#!/usr/bin/env python3
"""
Configuration module for Factor Worker
"""

import os
from typing import Optional


class Config:
    """Worker Configuration"""
    
    def __init__(self):
        # Redis Configuration
        self.redis_host: str = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port: int = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db: int = int(os.getenv('REDIS_DB', '0'))
        
        # RabbitMQ Configuration
        self.rabbitmq_host: str = os.getenv('RABBITMQ_HOST', 'localhost')
        self.rabbitmq_port: int = int(os.getenv('RABBITMQ_PORT', '5672'))
        self.rabbitmq_user: str = os.getenv('RABBITMQ_USER', 'trademind')
        self.rabbitmq_pass: str = os.getenv('RABBITMQ_PASS')
        self.rabbitmq_vhost: str = os.getenv('RABBITMQ_VHOST', 'trademind')
        
        # Master Configuration
        self.master_host: str = os.getenv('MASTER_HOST', '192.168.1.100')
        self.master_port: int = int(os.getenv('MASTER_PORT', '8080'))
        
        # Worker Configuration
        self.worker_id: str = os.getenv('WORKER_ID', 'factor-worker-01')
        self.worker_type: str = os.getenv('WORKER_TYPE', 'factor')
        
        # Logging
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
