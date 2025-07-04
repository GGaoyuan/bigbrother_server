#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCloudOS Flask应用部署脚本
适用于OpenCloudOS系统的Flask项目自动化部署
"""

import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path

class OpenCloudOSDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.app_name = "bigbrother_server"
        self.service_name = f"{self.app_name}.service"
        self.user = "flask"
        self.port = 5000
        
    def run_command(self, command, check=True, shell=True):
        """执行系统命令"""
        print(f"执行命令: {command}")
        try:
            result = subprocess.run(command, shell=shell, check=check, 
                                  capture_output=True, text=True)
            if result.stdout:
                print(f"输出: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败: {e}")
            print(f"错误输出: {e.stderr}")
            if check:
                sys.exit(1)
            return e
    
    def check_system(self):
        """检查系统环境"""
        print("=== 检查系统环境 ===")
        
        # 检查是否为OpenCloudOS
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read()
                if 'OpenCloudOS' not in content:
                    print("警告: 当前系统可能不是OpenCloudOS")
        except FileNotFoundError:
            print("警告: 无法确定系统类型")
        
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
        
        # 更新包管理器
        self.run_command("yum update -y")
        
        # 安装基础依赖
        dependencies = [
            "python3",
            "python3-pip",
            "python3-devel",
            "gcc",
            "gcc-c++",
            "make",
            "openssl-devel",
            "libffi-devel",
            "nginx",
            "supervisor"
        ]
        
        for dep in dependencies:
            self.run_command(f"yum install -y {dep}")
        
        # 启动并启用nginx
        self.run_command("systemctl start nginx")
        self.run_command("systemctl enable nginx")
        
        # 启动并启用supervisor
        self.run_command("systemctl start supervisord")
        self.run_command("systemctl enable supervisord")
    
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
        
        nginx_config = f"""server {{
    listen 80;
    server_name _;
    
    location / {{
        proxy_pass http://127.0.0.1:{self.port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    location /static {{
        alias /opt/{self.app_name}/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
    
    # 安全配置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}}
"""
        
        nginx_config_path = f"/etc/nginx/conf.d/{self.app_name}.conf"
        with open(nginx_config_path, 'w', encoding='utf-8') as f:
            f.write(nginx_config)
        
        # 测试nginx配置
        self.run_command("nginx -t")
    
    def create_supervisor_config(self):
        """创建Supervisor配置（备用方案）"""
        print("=== 创建Supervisor配置 ===")
        
        supervisor_config = f"""[program:{self.app_name}]
command=/home/{self.user}/venv/bin/gunicorn -c /opt/{self.app_name}/gunicorn.conf.py app:app
directory=/opt/{self.app_name}
user={self.user}
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/{self.app_name}/supervisor.log
environment=PATH="/home/{self.user}/venv/bin"
"""
        
        supervisor_config_path = f"/etc/supervisord.d/{self.app_name}.ini"
        with open(supervisor_config_path, 'w', encoding='utf-8') as f:
            f.write(supervisor_config)
    
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
            self.create_supervisor_config()
            self.create_health_check()
            self.start_services()
            self.create_deployment_info()
            
            print("\\n=== 部署完成 ===")
            print(f"应用名称: {self.app_name}")
            print(f"访问地址: http://localhost")
            print(f"应用端口: {self.port}")
            print(f"服务名称: {self.service_name}")
            print("\\n常用命令:")
            print(f"  查看服务状态: systemctl status {self.service_name}")
            print(f"  重启服务: systemctl restart {self.service_name}")
            print(f"  查看日志: journalctl -u {self.service_name} -f")
            print("  查看nginx状态: systemctl status nginx")
            
        except Exception as e:
            print(f"部署过程中出现错误: {e}")
            sys.exit(1)

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
OpenCloudOS Flask应用部署脚本

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
    
    deployer = OpenCloudOSDeployer()
    deployer.deploy()

if __name__ == "__main__":
    main()
