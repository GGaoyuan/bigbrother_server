from flask import Flask, jsonify
import psutil
import time

# 创建Flask应用
app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World! Flask应用运行正常'

@app.route('/test')
def test():
    return '测试页面'

@app.route('/health')
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

if __name__ == '__main__':
    app.run()