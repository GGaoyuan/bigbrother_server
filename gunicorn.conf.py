#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunicorn配置文件
适用于OpenCloudOS生产环境
"""

import multiprocessing
import os

# 服务器配置
bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# 日志配置
accesslog = "/var/log/bigbrother_server/access.log"
errorlog = "/var/log/bigbrother_server/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程配置
preload_app = True
daemon = False
pidfile = "/var/run/bigbrother_server.pid"

# 超时配置
timeout = 30
keepalive = 2
graceful_timeout = 30

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 性能配置
max_requests_jitter = 50
worker_tmp_dir = "/dev/shm"
forwarded_allow_ips = "127.0.0.1"

# 环境变量
raw_env = [
    "FLASK_ENV=production",
    "FLASK_APP=app.py"
]

# 钩子函数
def on_starting(server):
    """服务器启动时的钩子"""
    server.log.info("Gunicorn服务器正在启动...")

def on_reload(server):
    """重载时的钩子"""
    server.log.info("Gunicorn服务器正在重载...")

def worker_int(worker):
    """工作进程中断时的钩子"""
    worker.log.info("工作进程被中断")

def pre_fork(server, worker):
    """fork工作进程前的钩子"""
    server.log.info("准备fork工作进程")

def post_fork(server, worker):
    """fork工作进程后的钩子"""
    server.log.info(f"工作进程 {worker.pid} 已启动")

def post_worker_init(worker):
    """工作进程初始化后的钩子"""
    worker.log.info(f"工作进程 {worker.pid} 初始化完成")

def worker_abort(worker):
    """工作进程异常退出时的钩子"""
    worker.log.info(f"工作进程 {worker.pid} 异常退出")

def pre_exec(server):
    """执行前的钩子"""
    server.log.info("服务器准备执行")

def when_ready(server):
    """服务器就绪时的钩子"""
    server.log.info("Gunicorn服务器已就绪，可以接收请求")

def on_exit(server):
    """服务器退出时的钩子"""
    server.log.info("Gunicorn服务器正在退出") 