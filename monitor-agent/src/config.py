#!/usr/bin/env python3
"""
Configuration module for Monitor Agent
"""

import os


class Config:
    """Agent Configuration"""
    
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
        
        # Agent Configuration
        self.agent_id: str = os.getenv('AGENT_ID', 'monitor-agent-01')
        self.agent_type: str = os.getenv('AGENT_TYPE', 'monitor')
        
        # Logging
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
