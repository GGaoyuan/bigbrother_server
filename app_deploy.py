#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用部署脚本
适用于OpenCloudOS系统，使用Gunicorn + Nginx架构
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

class FlaskDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.app_name = "bigbrother_server"
        self.service_name = f"{self.app_name}.service"
        self.user = "flask"
        self.port = 5000
        
    def run_command(self, command, check=True, shell=True):
        """执行系统命令（实时输出）"""
        print(f"执行命令: {command}")
        try:
            process = subprocess.Popen(
                command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            while True:
                line = process.stdout.readline() if process.stdout else None
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line, end='')  # 实时输出
            retcode = process.poll()
            if check and retcode != 0:
                print(f"命令执行失败，退出码: {retcode}")
                sys.exit(1)
            return retcode
        except Exception as e:
            print(f"命令执行异常: {e}")
            if check:
                sys.exit(1)
            return -1
    
    def check_system(self):
        """检查系统环境"""
        print("=== 检查系统环境 ===")
        
        # 检查Python版本
        python_version = subprocess.run(['python3', '--version'], 
                                       capture_output=True, text=True)
        print(f"Python版本: {python_version.stdout.strip()}")
        
        # 检查是否为root用户
        if os.geteuid() != 0:
            print("警告: 建议使用root权限运行此脚本")
    
    def install_system_dependencies(self):
        """安装系统依赖"""
        print("=== 安装系统依赖 ===")
        
        # 检查并安装基础依赖
        dependencies = [
            "python3",
            "python3-pip", 
            "python3-devel",
            "gcc",
            "gcc-c++",
            "make",
            "openssl-devel",
            "libffi-devel",
            "nginx"
        ]
        
        for dep in dependencies:
            print(f"检查并安装: {dep}")
            self.run_command(f"yum install -y {dep}")
        
        # 启动并启用nginx
        self.run_command("systemctl start nginx")
        self.run_command("systemctl enable nginx")
        
        # 尝试安装和启动supervisor（可选）
        try:
            print("尝试安装supervisor...")
            self.run_command("yum install -y supervisor", check=False)
            
            # 检查supervisor是否安装成功
            result = subprocess.run(['systemctl', 'list-unit-files', 'supervisord.service'], 
                                  capture_output=True, text=True)
            if 'supervisord.service' in result.stdout:
                print("启动supervisor服务...")
                self.run_command("systemctl start supervisord")
                self.run_command("systemctl enable supervisord")
            else:
                print("supervisor未安装或不可用，跳过supervisor配置")
        except Exception as e:
            print(f"supervisor安装失败，跳过: {e}")
            print("注意: 应用将使用systemd管理，supervisor是可选的")
    
    def create_flask_user(self):
        """创建Flask应用用户"""
        print("=== 创建Flask应用用户 ===")
        
        # 检查用户是否已存在
        result = subprocess.run(['id', self.user], capture_output=True)
        if result.returncode != 0:
            self.run_command(f"useradd -r -s /bin/bash -d /home/{self.user} {self.user}")
            self.run_command(f"mkdir -p /home/{self.user}")
            self.run_command(f"chown {self.user}:{self.user} /home/{self.user}")
        else:
            print(f"用户 {self.user} 已存在")
    
    def setup_python_environment(self):
        """设置Python环境"""
        print("=== 设置Python环境 ===")
        
        # 创建虚拟环境目录
        venv_path = f"/home/{self.user}/venv"
        if not os.path.exists(venv_path):
            self.run_command(f"python3 -m venv {venv_path}")
        
        # 设置权限
        self.run_command(f"chown -R {self.user}:{self.user} {venv_path}")
        
        # 激活虚拟环境并安装依赖
        pip_cmd = f"{venv_path}/bin/pip"
        self.run_command(f"{pip_cmd} install --upgrade pip")
        self.run_command(f"{pip_cmd} install -r {self.project_root}/requirements.txt")
        
        # 安装额外的生产依赖
        production_deps = [
            "gunicorn",
            "gevent",
            "psutil"
        ]
        
        for dep in production_deps:
            self.run_command(f"{pip_cmd} install {dep}")
    
    def deploy_application(self):
        """部署应用"""
        print("=== 部署应用 ===")
        
        # 创建应用目录
        app_dir = f"/opt/{self.app_name}"
        self.run_command(f"mkdir -p {app_dir}")
        
        # 复制应用文件
        self.run_command(f"cp -r {self.project_root}/* {app_dir}/")
        
        # 设置权限
        self.run_command(f"chown -R {self.user}:{self.user} {app_dir}")
        self.run_command(f"chmod +x {app_dir}/app.py")
    
    def create_gunicorn_config(self):
        """创建Gunicorn配置"""
        print("=== 创建Gunicorn配置 ===")
        
        gunicorn_config = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing

# 服务器配置
bind = "127.0.0.1:{self.port}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# 日志配置
accesslog = "/var/log/{self.app_name}/access.log"
errorlog = "/var/log/{self.app_name}/error.log"
loglevel = "info"

# 进程配置
preload_app = True
daemon = False

# 超时配置
timeout = 30
keepalive = 2

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
"""
        
        # 创建日志目录
        log_dir = f"/var/log/{self.app_name}"
        self.run_command(f"mkdir -p {log_dir}")
        self.run_command(f"chown {self.user}:{self.user} {log_dir}")
        
        # 写入配置文件
        config_path = f"/opt/{self.app_name}/gunicorn.conf.py"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(gunicorn_config)
        
        self.run_command(f"chown {self.user}:{self.user} {config_path}")
    
    def create_systemd_service(self):
        """创建systemd服务"""
        print("=== 创建systemd服务 ===")
        
        service_content = f"""[Unit]
Description={self.app_name} Flask Application
After=network.target

[Service]
Type=exec
User={self.user}
Group={self.user}
WorkingDirectory=/opt/{self.app_name}
Environment=PATH=/home/{self.user}/venv/bin
ExecStart=/home/{self.user}/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
        
        service_path = f"/etc/systemd/system/{self.service_name}"
        with open(service_path, 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        # 重新加载systemd配置
        self.run_command("systemctl daemon-reload")
        self.run_command(f"systemctl enable {self.service_name}")
    
    def create_nginx_config(self):
        """创建Nginx配置"""
        print("=== 创建Nginx配置 ===")
        
        nginx_config = f"""upstream flask_app {{
    server 127.0.0.1:{self.port};
    keepalive 32;
}}

server {{
    listen 80;
    server_name _;
    
    # 客户端最大请求体大小
    client_max_body_size 10M;
    
    # 超时设置
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # 缓冲设置
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    proxy_busy_buffers_size 8k;
    
    # 主要应用路由
    location / {{
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
    }}
    
    # 静态文件处理
    location /static {{
        alias /opt/{self.app_name}/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }}
    
    # 健康检查端点
    location /health {{
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }}
    
    # 安全头设置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # 隐藏Nginx版本
    server_tokens off;
    
    # 日志配置
    access_log /var/log/nginx/{self.app_name}_access.log;
    error_log /var/log/nginx/{self.app_name}_error.log;
}}
"""
        
        nginx_config_path = f"/etc/nginx/conf.d/{self.app_name}.conf"
        with open(nginx_config_path, 'w', encoding='utf-8') as f:
            f.write(nginx_config)
        
        # 测试nginx配置
        self.run_command("nginx -t")
    
    def start_services(self):
        """启动服务"""
        print("=== 启动服务 ===")
        
        # 启动Flask应用
        self.run_command(f"systemctl start {self.service_name}")
        
        # 重启nginx
        self.run_command("systemctl restart nginx")
        
        # 检查服务状态
        self.run_command(f"systemctl status {self.service_name}")
        self.run_command("systemctl status nginx")
    
    def create_health_check(self):
        """创建健康检查脚本"""
        print("=== 创建健康检查脚本 ===")
        
        health_check_script = f"""#!/bin/bash
# 健康检查脚本

APP_URL="http://localhost:{self.port}/health"
LOG_FILE="/var/log/{self.app_name}/health.log"

# 检查应用是否响应
response=$(curl -s -o /dev/null -w "%{{http_code}}" $APP_URL)

if [ $response -eq 200 ]; then
    echo "$(date): 应用运行正常" >> $LOG_FILE
    exit 0
else
    echo "$(date): 应用无响应，HTTP状态码: $response" >> $LOG_FILE
    # 重启服务
    systemctl restart {self.service_name}
    exit 1
fi
"""
        
        health_script_path = f"/opt/{self.app_name}/health_check.sh"
        with open(health_script_path, 'w', encoding='utf-8') as f:
            f.write(health_check_script)
        
        self.run_command(f"chmod +x {health_script_path}")
        self.run_command(f"chown {self.user}:{self.user} {health_script_path}")
    
    def create_deployment_info(self):
        """创建部署信息文件"""
        print("=== 创建部署信息 ===")
        
        deployment_info = {
            "app_name": self.app_name,
            "deployment_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user": self.user,
            "port": self.port,
            "app_directory": f"/opt/{self.app_name}",
            "service_name": self.service_name,
            "nginx_config": f"/etc/nginx/conf.d/{self.app_name}.conf",
            "log_directory": f"/var/log/{self.app_name}",
            "health_check_script": f"/opt/{self.app_name}/health_check.sh"
        }
        
        info_path = f"/opt/{self.app_name}/deployment_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(deployment_info, f, indent=2, ensure_ascii=False)
        
        self.run_command(f"chown {self.user}:{self.user} {info_path}")
    
    def deploy(self):
        """执行完整部署流程"""
        print("开始部署Flask应用到OpenCloudOS...")
        
        try:
            self.check_system()
            self.install_system_dependencies()
            self.create_flask_user()
            self.setup_python_environment()
            self.deploy_application()
            self.create_gunicorn_config()
            self.create_systemd_service()
            self.create_nginx_config()
            self.create_health_check()
            self.start_services()
            self.create_deployment_info()
            
            print("\n=== 部署完成 ===")
            print(f"应用名称: {self.app_name}")
            print(f"访问地址: http://localhost")
            print(f"应用端口: {self.port}")
            print(f"服务名称: {self.service_name}")
            print("\n常用命令:")
            print(f"  查看服务状态: systemctl status {self.service_name}")
            print(f"  重启服务: systemctl restart {self.service_name}")
            print(f"  查看日志: journalctl -u {self.service_name} -f")
            print(f"  查看nginx状态: systemctl status nginx")
            print(f"  健康检查: curl http://localhost/health")
            
        except Exception as e:
            print(f"部署过程中出现错误: {e}")
            sys.exit(1)

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Flask应用部署脚本

用法:
    python3 app_deploy.py          # 执行完整部署
    python3 app_deploy.py --help   # 显示帮助信息

功能:
    - 安装系统依赖
    - 创建Flask用户
    - 配置Python环境
    - 部署Flask应用
    - 配置Gunicorn
    - 创建systemd服务
    - 配置Nginx反向代理
    - 创建健康检查脚本

注意: 建议使用root权限运行此脚本
        """)
        return
    
    deployer = FlaskDeployer()
    deployer.deploy()

if __name__ == "__main__":
    main()
