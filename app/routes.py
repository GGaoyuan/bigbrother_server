from flask import Blueprint, jsonify
import psutil
import time

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return 'Hello, World!111111'


@bp.route('/testaaa')
def test():
    return 'testaaa'

@bp.route('/hahaha')
def hahaha():
    return 'aaaaaaaaaaa666666666'


@bp.route('/health')
def health_check():
    """健康检查端点"""
    try:
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            }
        }
        
        return jsonify(health_data), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500