#!/usr/bin/env python3
"""
GPU Monitoring for AGX Xavier
NVIDIA Jetson specific GPU metrics
"""

import os
import subprocess
from typing import Dict, Any, Optional
from loguru import logger


class GPUMonitor:
    """GPU Monitor for NVIDIA Jetson AGX Xavier"""
    
    def __init__(self):
        self.is_jetson = self._detect_jetson()
        self.has_tegrastats = self._check_tegrastats()
        
    def _detect_jetson(self) -> bool:
        """Detect if running on Jetson device"""
        try:
            # Check for Jetson-specific files
            if os.path.exists('/etc/nv_tegra_release'):
                return True
            if os.path.exists('/sys/class/tegra-fuse'):
                return True
            
            # Check model name
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                if 'NVIDIA Jetson' in model or 'NVIDIA Orin' in model:
                    return True
        except Exception:
            pass
        return False
    
    def _check_tegrastats(self) -> bool:
        """Check if tegrastats is available"""
        try:
            result = subprocess.run(
                ['which', 'tegrastats'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        if not self.is_jetson:
            return {'error': 'Not running on Jetson device'}
        
        try:
            # Read Jetson model info
            model = self._get_jetson_model()
            
            return {
                'model': model,
                'is_jetson': self.is_jetson,
                'has_tegrastats': self.has_tegrastats,
                'cuda_arch': self._get_cuda_arch(),
                'gpu_name': self._get_gpu_name()
            }
        except Exception as e:
            logger.error(f"Failed to get GPU info: {e}")
            return {'error': str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get GPU metrics"""
        if not self.is_jetson:
            return {}
        
        try:
            if self.has_tegrastats:
                return self._get_tegrastats_metrics()
            else:
                return self._get_fallback_metrics()
        except Exception as e:
            logger.error(f"Failed to get GPU metrics: {e}")
            return {}
    
    def _get_tegrastats_metrics(self) -> Dict[str, Any]:
        """Get metrics from tegrastats"""
        try:
            # Run tegrastats once
            result = subprocess.run(
                ['tegrastats', '--interval', '100', '--count', '1'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode != 0:
                return {}
            
            stats = result.stdout.strip()
            
            # Parse tegrastats output
            metrics = self._parse_tegrastats(stats)
            return metrics
            
        except Exception as e:
            logger.error(f"tegrastats failed: {e}")
            return {}
    
    def _parse_tegrastats(self, stats: str) -> Dict[str, Any]:
        """Parse tegrastats output"""
        metrics = {}
        
        try:
            # RAM usage
            if 'RAM' in stats:
                ram_parts = stats.split('RAM')[1].split()[0]
                if '/' in ram_parts:
                    used, total = ram_parts.split('/')
                    metrics['ram_used_mb'] = int(used.replace('MB', ''))
                    metrics['ram_total_mb'] = int(total.replace('MB', ''))
            
            # GPU usage
            if 'GR3D_FREQ' in stats:
                gr3d_parts = stats.split('GR3D_FREQ')[1].split()[0]
                if '%' in gr3d_parts:
                    metrics['gpu_percent'] = int(gr3d_parts.replace('%', ''))
            
            # Temperatures
            temps = {}
            if 'PLL@' in stats:
                temps['pll'] = self._extract_temp(stats, 'PLL')
            if 'CPU@' in stats:
                temps['cpu'] = self._extract_temp(stats, 'CPU')
            if 'PMIC@' in stats:
                temps['pmic'] = self._extract_temp(stats, 'PMIC')
            if 'AO@' in stats:
                temps['ao'] = self._extract_temp(stats, 'AO')
            if 'thermal@' in stats:
                temps['thermal'] = self._extract_temp(stats, 'thermal')
            
            if temps:
                metrics['temperatures'] = temps
                metrics['temperature'] = max(temps.values()) if temps else None
            
            # Power consumption
            if 'VDD_IN' in stats:
                metrics['vdd_in'] = self._extract_power(stats, 'VDD_IN')
            if 'VDD_CPU_GPU' in stats:
                metrics['vdd_cpu_gpu'] = self._extract_power(stats, 'VDD_CPU_GPU')
            if 'VDD_SOC' in stats:
                metrics['vdd_soc'] = self._extract_power(stats, 'VDD_SOC')
            if 'VDD_CV' in stats:
                metrics['vdd_cv'] = self._extract_power(stats, 'VDD_CV')
            
            # Memory usage (if available)
            if 'RAM' in stats:
                ram_info = stats.split('RAM')[1].split('/')[0].strip()
                metrics['memory_used'] = int(ram_info.replace('MB', ''))
        
        except Exception as e:
            logger.error(f"Failed to parse tegrastats: {e}")
        
        return metrics
    
    def _extract_temp(self, stats: str, prefix: str) -> Optional[float]:
        """Extract temperature from tegrastats"""
        try:
            key = f'{prefix}@'
            if key in stats:
                temp_str = stats.split(key)[1].split('C')[0].strip()
                return float(temp_str)
        except:
            pass
        return None
    
    def _extract_power(self, stats: str, rail: str) -> Optional[float]:
        """Extract power consumption from tegrastats"""
        try:
            key = f'{rail}'
            if key in stats:
                parts = stats.split(key)[1].split('/')[0].strip()
                if 'mW' in parts:
                    return float(parts.replace('mW', ''))
        except:
            pass
        return None
    
    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Get metrics from fallback sources"""
        metrics = {}
        
        try:
            # Try to read GPU frequency
            gpu_path = '/sys/class/devfreq/17000000.gp10b'
            if os.path.exists(gpu_path):
                # Read cur_freq
                with open(f'{gpu_path}/cur_freq', 'r') as f:
                    metrics['gpu_freq'] = int(f.read().strip())
        except:
            pass
        
        return metrics
    
    def _get_jetson_model(self) -> str:
        """Get Jetson model name"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                return f.read().strip().replace('\x00', '')
        except:
            return 'Unknown'
    
    def _get_cuda_arch(self) -> int:
        """Get CUDA architecture version"""
        # AGX Xavier is sm_72
        model = self._get_jetson_model().lower()
        if 'xavier' in model:
            return 72
        elif 'orin' in model:
            return 87
        elif 'nano' in model:
            return 53
        elif 'tx1' in model or 'tx2' in model:
            return 62
        return 72  # Default to Xavier
    
    def _get_gpu_name(self) -> str:
        """Get GPU name"""
        model = self._get_jetson_model().lower()
        if 'agx xavier' in model:
            return 'Volta GV10B'
        elif 'xavier nx' in model:
            return 'Volta GV10B'
        elif 'orin' in model:
            return 'Ampere GA10B'
        elif 'nano' in model:
            return 'Maxwell GM20B'
        elif 'tx2' in model:
            return 'Pascal GP10B'
        return 'Unknown'
